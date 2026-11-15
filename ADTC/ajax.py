
import os
import re
import subprocess
import uuid

from flask_restful import Resource, fields, marshal_with, request

from ADTC import api, app
from ADTC.core import mongo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = os.path.join(BASE_DIR, 'static', 'ADTC', 'analysis_result_tmp_file')
SURVIVAL_SCRIPT = os.path.join(BASE_DIR, 'script', 'survival.R')

CANCER_TYPES = {'BLCA', 'BRCA', 'CESC', 'COAD', 'DLBC', 'ESCA', 'HNSC', 'KIRC', 'KIRP',
                'LGG', 'LIHC', 'LUAD', 'LUSC', 'OV', 'PAAD', 'PRAD', 'SARC', 'STAD',
                'THCA', 'THYM', 'UCEC'}
ANCESTRIES = {'eur', 'afr', 'eas'}
TAGS = {'lncRNA', 'AS', 'APA', 'Editing'}
SAFE_FEATURE = re.compile(r'^[A-Za-z0-9_.:;|+-]{1,500}$')

EDITING_GENE = 'Gene_wgEncodeGencodeBasicV34'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cancer_code(value):
    """Front end sends e.g. '(BLCA) Bladder ...' or 'BLCA'; return the code."""
    return value.split(')')[0].replace('(', '')


def _parse_cancer(value):
    """Like _cancer_code, but tolerant of a missing value and surrounding spaces."""
    return _cancer_code(value or '').strip()


def _number(value):
    """Return value as a string if it parses as a number, else raise."""
    float(value)
    return str(value)


def _regex(pattern, value):
    """Case-insensitive MongoDB regex with `value` escaped into `pattern`."""
    return {'$regex': pattern.format(re.escape(value or '')), '$options': 'i'}


def _result_list(key, result_fields):
    return {key: fields.List(fields.Nested(result_fields))}


# ---------------------------------------------------------------------------
# Survival results table
# ---------------------------------------------------------------------------

Survival_result = {
    'cancertypes': fields.String,
    'ancestry': fields.String,
    'feature': fields.String,

    'gene_name': fields.String,
    'event_type': fields.String,
    'event_chr': fields.String,
    'event_coordinates': fields.String,
    'alt_region_coordinates': fields.String,

    'transcript': fields.String,
    'position': fields.String,

    'type': fields.String,
    'repeat': fields.String,
    EDITING_GENE: fields.String,

    'HR_p': fields.Float,
    'HR': fields.Float,
    'Up95': fields.String,   # String to avoid an error on Inf
    'Low95': fields.String,  # String to avoid an error on Inf
    'Prognosis': fields.String,
    'low_N': fields.Float,
    'high_N': fields.Float,
    'N': fields.Float,
    'FDR': fields.Float,
    'tag': fields.String,
}

# tag -> (collection, field matched exactly, request argument holding the gene)
SURVIVAL_SOURCES = {
    'lncRNA': ('survive_res_lnc', 'gene_name', 'gene_name'),
    'AS': ('survive_res_as', 'gene_name', 'gene_name'),
    'APA': ('survive_res_apa', 'gene_name', 'gene_name'),
    'Editing': ('survive_res_editing', EDITING_GENE, 'gene_name2'),
}


class ADTC_Survival_result(Resource):
    @marshal_with(_result_list('Survival_result_list', Survival_result))
    def get(self):
        condition = [{'$match': {'cancertypes': _cancer_code(request.args.get('cancertypes'))}}]

        event_type = request.args.get('event_type')
        if event_type:
            condition.append({'$match': {'event_type': _cancer_code(event_type)}})

        res = []
        source = SURVIVAL_SOURCES.get(request.args.get('tag'))
        if source:
            collection, field, arg = source
            condition.append({'$match': {field: _regex('^{0}$', request.args.get(arg))}})
            res = list(mongo.db[collection].aggregate(condition))

        return {'Survival_result_list': res}


api.add_resource(ADTC_Survival_result, '/api/survival_r')


# ---------------------------------------------------------------------------
# Custom survival plot (runs script/survival.R)
# ---------------------------------------------------------------------------

class Survival(Resource):
    def get(self):
        cancer = _parse_cancer(request.args.get('cancertypes'))
        ancestry = request.args.get('ancestry', '')
        feature = request.args.get('feature', '')
        tag = request.args.get('tag', '')
        if (cancer not in CANCER_TYPES or ancestry not in ANCESTRIES
                or tag not in TAGS or not SAFE_FEATURE.match(feature)):
            return {'message': 'invalid parameters'}, 400
        try:
            hr = _number(request.args.get('HR'))
            hr_p = _number(request.args.get('HR_p'))
            n_high = _number(request.args.get('high_N'))
            n_low = _number(request.args.get('low_N'))
        except (TypeError, ValueError):
            return {'message': 'invalid parameters'}, 400

        uuid_str = str(uuid.uuid4())
        out_dir = os.path.join(TMP_DIR, uuid_str)
        os.makedirs(out_dir)

        cmd = [app.config['RSCRIPT'], SURVIVAL_SCRIPT, cancer, ancestry, feature, tag,
               hr, hr_p, n_high, n_low, out_dir, app.config['DATA_DIR']]
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return {'path': '/static/ADTC/analysis_result_tmp_file/' + uuid_str}


api.add_resource(Survival, '/api/survival')


# ---------------------------------------------------------------------------
# lncRNA targets
# ---------------------------------------------------------------------------

lncRNATarget_result = {
    'class': fields.String,
    'type': fields.String,
    'Drug_Name': fields.String,
    'ENSEMBL_ID': fields.String,
    'gene_name': fields.String,
    'tag': fields.String,
    'pvalue': fields.Float,
    'fdr': fields.Float,
    'coef_sig': fields.Float,
    'Source': fields.String,
}


class ADTC_lncRNATarget_result(Resource):
    @marshal_with(_result_list('lncRNATarget_result_list', lncRNATarget_result))
    def get(self):
        return {'lncRNATarget_result_list': list(mongo.db.lnc_target.find())}


api.add_resource(ADTC_lncRNATarget_result, '/api/lncrna_target')


# ---------------------------------------------------------------------------
# Differential analysis (PSM) results: lncRNA, AS, APA, Editing
# ---------------------------------------------------------------------------

class _PSMResult(Resource):
    """Filter a *_psm collection by cancer type, gene prefix and comparison."""
    collection = None
    list_key = None
    gene_field = 'gene_name'

    def get(self):
        gene = request.args.get('gene')
        compare = request.args.get('compare')

        condition = [{'$match': {'cancertype': _cancer_code(request.args.get('cancer_types'))}}]
        if gene:
            condition.append({'$match': {self.gene_field: _regex('^{0}', gene)}})
        if compare and compare != 'all':
            condition.append({'$match': {'type': _regex('^{0}', compare)}})

        return {self.list_key: list(mongo.db[self.collection].aggregate(condition))}


lncRNA_result = {
    'cancertype': fields.String,
    'type': fields.String,
    'feature_sig': fields.String,
    'gene_name': fields.String,
    'mean1_sig_w': fields.Float,
    'mean0_sig_w': fields.Float,
    'mean1_sig': fields.Float,
    'mean0_sig': fields.Float,
    'fdr_sig': fields.Float,
    'coef_sig': fields.Float,
    'alteration': fields.String,
}

AS_result = {
    'cancertype': fields.String,
    'type': fields.String,
    'feature_sig': fields.String,
    'gene_id': fields.String,
    'gene_name': fields.String,
    'event_type': fields.String,
    'event_chr': fields.String,
    'event_coordinates': fields.String,
    'alt_region_coordinates': fields.String,
    'mean1_sig_w': fields.Float,
    'mean0_sig_w': fields.Float,
    'mean1_sig': fields.Float,
    'mean0_sig': fields.Float,
    'diff': fields.Float,
    'fdr_sig': fields.Float,
    'coef_sig': fields.Float,
    'alteration': fields.String,
}

APA_result = {
    'cancertype': fields.String,
    'type': fields.String,
    'feature_sig': fields.String,
    'gene_name': fields.String,
    'transcript': fields.String,
    'position': fields.String,
    'mean1_sig_w': fields.Float,
    'mean0_sig_w': fields.Float,
    'mean1_sig': fields.Float,
    'mean0_sig': fields.Float,
    'fdr_sig': fields.Float,
    'diff': fields.Float,
    'alteration': fields.String,
}

Editing_result = {
    'cancertype': fields.String,
    'type': fields.String,
    'feature_sig': fields.String,
    'Type': fields.String,
    EDITING_GENE: fields.String,  # gene name
    'repeat_': fields.String,
    'mean1_sig_w': fields.Float,
    'mean0_sig_w': fields.Float,
    'mean1_sig': fields.Float,
    'mean0_sig': fields.Float,
    'fdr_sig': fields.Float,
    'diff': fields.Float,
    'alteration': fields.String,
}


class ADTC_lncRNA_result(_PSMResult):
    collection = 'lncrna_psm'
    list_key = 'lncRNA_result_list'
    method_decorators = [marshal_with(_result_list(list_key, lncRNA_result))]


class ADTC_AS_result(_PSMResult):
    collection = 'as_psm'
    list_key = 'AS_result_list'
    method_decorators = [marshal_with(_result_list(list_key, AS_result))]


class ADTC_APA_result(_PSMResult):
    collection = 'apa_psm'
    list_key = 'APA_result_list'
    method_decorators = [marshal_with(_result_list(list_key, APA_result))]


class ADTC_Editing_result(_PSMResult):
    collection = 'editing_psm'
    list_key = 'Editing_result_list'
    gene_field = EDITING_GENE
    method_decorators = [marshal_with(_result_list(list_key, Editing_result))]


api.add_resource(ADTC_lncRNA_result, '/api/lncrna_r')
api.add_resource(ADTC_AS_result, '/api/as_r')
api.add_resource(ADTC_APA_result, '/api/apa_r')
api.add_resource(ADTC_Editing_result, '/api/editing_r')


# ---------------------------------------------------------------------------
# Per-sample values of one feature, split by two ancestries (box plot)
# ---------------------------------------------------------------------------

Transcriptome = {
    'value1': fields.String,
    'value2': fields.String,
    'name1': fields.String,
    'name2': fields.String,
}

# compare -> ((display name, ancestry code), (display name, ancestry code))
ANCESTRY_PAIRS = {
    'afr_eas': (('African', 'afr'), ('Asian', 'eas')),
    'eur_afr': (('European', 'eur'), ('African', 'afr')),
    'eur_eas': (('European', 'eur'), ('Asian', 'eas')),
}

# Signature -> (collection, field holding the feature id)
FEATURE_SOURCES = {
    'lncRNA': ('ADTC_lncRNAdata', 'gene'),
    'AS': ('ADTC_ASdata', 'event_id'),
    'APA': ('ADTC_APAdata', 'event_id'),
    'Editing': ('ADTC_Editingdata', 'event_id'),
}


class Transcriptomedata(Resource):
    @marshal_with(Transcriptome)
    def get(self):
        cancer = request.args.get('cancer_types')
        (name1, ancestry1), (name2, ancestry2) = ANCESTRY_PAIRS[request.args.get('compare')]
        collection, id_field = FEATURE_SOURCES[request.args.get('Signature')]

        def barcodes(ancestry):
            query = [{'$match': {'cancer_types': cancer, 'ancestry': ancestry}}]
            return [item['barcode'] for item in mongo.db.ADTC_clinic_info.aggregate(query)]

        # One document per feature; its keys are sample barcodes.
        record = list(mongo.db[collection].aggregate(
            [{'$match': {id_field: request.args.get('gene')}}]))[0]

        def values(ancestry):
            return ','.join(str(record[key]) for key in barcodes(ancestry) if key in record)

        return {'value1': values(ancestry1), 'value2': values(ancestry2),
                'name1': name1, 'name2': name2}


api.add_resource(Transcriptomedata, '/api/transcriptome_detail')
