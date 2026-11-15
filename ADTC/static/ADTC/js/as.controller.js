'use strict';

angular.module('ADTC')
    .controller('ASController', ASController);

function ASController($scope, $http, ADTCService, AS_GENES) {
    var base_url = ADTCService.getAPIBaseUrl();

    ADTCService.initTabs($scope, ['One', 'Two']);
    ADTCService.autocomplete('#gene', AS_GENES);

    // Differential analysis
    $scope.search = function () {
        $scope.table_show = 0;
        $scope.loading = 1;
        $http({
            url: base_url + '/api/as_r',
            method: 'GET',
            params: {
                'cancer_types': $('#cancer_types').val(),
                'compare': $('#compare').val(),
                'gene': $('#gene').val()
            }
        }).then(function (response) {
            $scope.AS_result_list = response.data.AS_result_list;
            $scope.table_show = 1;
            $scope.loading = 0;
            ADTCService.dataTable('#tablesort');
        });
    };

    // Survival analysis
    $scope.search2 = function () {
        $scope.table_show2 = 0;
        $scope.loading2 = 1;
        $http({
            url: base_url + '/api/survival_r',
            method: 'GET',
            params: {
                'cancertypes': $('#cancertypes').val(),
                'gene_name': $('#gene_name').val(),
                'tag': 'AS',
                'event_type': $('#event_type').val()
            }
        }).then(function (response) {
            $scope.Survival_result_list = response.data.Survival_result_list;
            $scope.table_show2 = 1;
            $scope.loading2 = 0;
            ADTCService.dataTable('#tablesort2');
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
                'Signature': 'AS'
            }
        }).then(function (response) {
            $scope.load = 0;
            ADTCService.ancestryBoxPlot(dat, response.data, {
                title: dat['gene_name'],
                yTitle: 'PSI',
                transform: Number
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
