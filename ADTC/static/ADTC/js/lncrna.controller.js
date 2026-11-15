'use strict';

angular.module('ADTC')
    .controller('lncRNAController', lncRNAController);

function lncRNAController($scope, $http, ADTCService, LNCRNA_GENES, LNCRNA_SURVIVAL_GENES) {
    var base_url = ADTCService.getAPIBaseUrl();

    $scope.Math = Math;  // used by the template to back-transform log2 values

    ADTCService.initTabs($scope, ['One', 'Two', 'Three']);
    ADTCService.autocomplete('#gene', LNCRNA_GENES);
    ADTCService.autocomplete('#gene_name', LNCRNA_SURVIVAL_GENES);

    // lncRNA targets (loaded once)
    $http({
        url: base_url + '/api/lncrna_target',
        method: 'GET',
        params: {}
    }).then(function (response) {
        $scope.lncRNATarget_result_list = response.data.lncRNATarget_result_list;
        ADTCService.dataTable('#Tablesort');
    });

    // Differential analysis
    $scope.search = function () {
        $scope.table_show = 0;
        $scope.loading = 1;
        $http({
            url: base_url + '/api/lncrna_r',
            method: 'GET',
            params: {
                'cancer_types': $('#cancer_types').val(),
                'compare': $('#compare').val(),
                'gene': $('#gene').val()
            }
        }).then(function (response) {
            $scope.lncRNA_result_list = response.data.lncRNA_result_list;
            $scope.table_show = 1;
            $scope.loading = 0;
            ADTCService.dataTable('#tablesort');
        });
    };

    // Survival analysis
    $scope.search2 = function () {
        $scope.table_show3 = 0;
        $scope.loading3 = 1;
        $http({
            url: base_url + '/api/survival_r',
            method: 'GET',
            params: {
                'cancertypes': $('#cancertypes').val(),
                'gene_name': $('#gene_name').val(),
                'tag': 'lncRNA'
            }
        }).then(function (response) {
            $scope.Survival_result_list = response.data.Survival_result_list;
            $scope.table_show3 = 1;
            $scope.loading3 = 0;
            ADTCService.dataTable('#tablesort3');
        });
    };

    $scope.plot_box = function (dat) {
        $scope.load = 1;
        $http({
            url: base_url + '/api/transcriptome_detail',
            method: 'GET',
            params: {
                'compare': dat['type'],
                'gene': dat['feature_sig'],
                'cancer_types': dat['cancertype'],
                'Signature': 'lncRNA'
            }
        }).then(function (response) {
            $scope.load = 0;
            ADTCService.ancestryBoxPlot(dat, response.data, {
                title: dat['gene_name'],
                yTitle: 'log2(TPM+0.01)',
                transform: function (x) {
                    return Math.log2(Number(x) + 0.01);
                }
            });
        });
    };

    $scope.survival_plot = function (survive) {
        $scope.load2 = 1;
        $http({
            url: base_url + '/api/survival',
            method: 'GET',
            params: {
                'cancertypes': survive['cancertypes'],
                'ancestry': survive['ancestry'],
                'feature': survive['feature'],
                'tag': survive['tag'],
                'HR': survive['HR'],
                'HR_p': survive['FDR'],
                'high_N': survive['high_N'],
                'low_N': survive['low_N']
            }
        }).then(function (response) {
            $scope.reuslt = response.data.path;
            $scope.load2 = 0;
        });
    };
}
