'use strict';

angular.module('ADTC', ['ui.bootstrap', 'ngRoute', 'pageslide-directive', 'ui.bootstrap-slider', 'bw.paging', 'angularFileUpload'])
    .config(function ($routeProvider) {
        $routeProvider
            .when('/', {templateUrl: '/static/ADTC/pages/home.html', controller: 'HomeController'})
            .when('/lncrna', {templateUrl: '/static/ADTC/pages/lncrna.html', controller: 'lncRNAController'})
            .when('/as', {templateUrl: '/static/ADTC/pages/as.html', controller: 'ASController'})
            .when('/apa', {templateUrl: '/static/ADTC/pages/apa.html', controller: 'APAController'})
            .when('/editing', {templateUrl: '/static/ADTC/pages/editing.html', controller: 'EditingController'})
            .when('/download', {templateUrl: '/static/ADTC/pages/download.html', controller: 'DownloadController'})
            .when('/document', {templateUrl: '/static/ADTC/pages/document.html', controller: 'DocumentController'})
            .when('/contact', {templateUrl: '/static/ADTC/pages/contact.html', controller: 'ContactController'})
            .otherwise({redirectTo: '/404.html'});
    })
    .config(function ($interpolateProvider) {
        // Use {$ ... $} so templates do not clash with Jinja2's {{ ... }}.
        $interpolateProvider.startSymbol('{$');
        $interpolateProvider.endSymbol('$}');
    })
    .service('ADTCService', ADTCService);


// jQuery UI autocomplete that groups suggestions under a category header.
$.widget('custom.catcomplete', $.ui.autocomplete, {
    _create: function () {
        this._super();
        this.widget().menu('option', 'items', '> :not(.ui-autocomplete-category)');
    },
    _renderMenu: function (ul, items) {
        var that = this;
        var currentCategory = '';
        $.each(items, function (index, item) {
            if (item.category != currentCategory) {
                ul.append("<li class='ui-autocomplete-category'>" + item.category + '</li>');
                currentCategory = item.category;
            }
            var li = that._renderItemData(ul, item);
            if (item.category) {
                li.attr('aria-label', item.category + ' : ' + item.label);
            }
        });
    }
});


function ADTCService() {
    this.getAPIBaseUrl = function () {
        return '';
    };

    // Tabs: Show_res('Two') shows the "Two" panel and hides the others.
    this.initTabs = function ($scope, names) {
        $scope.Show_res = function (refer) {
            names.forEach(function (name) {
                $scope[name] = 0;
            });
            if (names.indexOf(refer) !== -1) {
                $scope[refer] = 1;
            }
        };
        $scope[names[0]] = 1;
    };

    // Attach a gene-name autocomplete to an <input>.
    this.autocomplete = function (selector, labels) {
        var source = labels.map(function (label) {
            return {category: 'gene name', label: label};
        });
        $(function () {
            $(selector).catcomplete({
                delay: 0,
                limit: 10,
                source: source,
                minLength: 1
            });
        });
    };

    // (Re)build a DataTable after Angular has rendered the new rows.
    this.dataTable = function (selector) {
        $(selector).DataTable().destroy();
        $(document).ready(function () {
            $(selector).DataTable({
                destroy: true,
                scrollX: true
            });
        });
    };

    // Box plot of one feature in two ancestry groups, drawn into #ancestry.
    // `opts`: {title, yTitle, transform(x) -> Number}
    this.ancestryBoxPlot = function (dat, response, opts) {
        var colors = {
            eur_eas: ['red', 'orange'],
            eur_afr: ['red', 'blue'],
            afr_eas: ['blue', 'orange']
        }[dat['type']] || [];

        var groups = [
            {values: response.value1.split(','), name: response.name1, color: colors[0]},
            {values: response.value2.split(','), name: response.name2, color: colors[1]}
        ];

        var data = [];
        groups.forEach(function (group) {
            if (group.values.length > 1) {
                data.push({
                    y: group.values.map(function (x) {
                        return opts.transform(x).toFixed(4);
                    }),
                    type: 'box',
                    name: group.name + ' (N=' + group.values.length + ')',
                    boxpoints: 'all',
                    jitter: 0.3,
                    whiskerwidth: 0.2,
                    pointpos: 0,
                    marker: {color: group.color, size: 2},
                    line: {width: 2}
                });
            }
        });

        var axis = {
            mirror: true,
            ticks: 'outside',
            showline: true,
            showgrid: false,
            linewidth: 2,
            zeroline: false
        };

        var layout = {
            title: opts.title + ' in ' + dat['cancertype'] + '<br>' + ' FDR = ' + Number(dat['fdr_sig']).toPrecision(2),
            width: 700,
            height: 600,
            font: {size: 18},
            yaxis: angular.extend({
                title: {text: opts.yTitle, font: {size: 20, color: '#000'}}
            }, axis),
            xaxis: angular.extend({
                title: {text: response.name1 + ' is ' + dat['alteration'], font: {size: 20}}
            }, axis),
            paper_bgcolor: 'white',
            plot_bgcolor: 'white',
            showlegend: false
        };

        Plotly.newPlot('ancestry', data, layout);
    };
}
