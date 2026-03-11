/* votes_charts.js — dc.js + crossfilter voting analysis charts */
(function () {
    'use strict';

    var GROUP = 'uvotes';
    var _charts = [];

    function cleanup() {
        _charts.forEach(function (c) {
            try { dc.chartRegistry.deregister(c, GROUP); } catch (e) {}
        });
        _charts = [];
    }

    function posColor(key) {
        var map = { yes: '#27ae60', no: '#e74c3c', abstain: '#f39c12', absent: '#95a7b5' };
        return map[key] || '#aaa';
    }

    window.VoteCharts = {

        init: function (containerSel, votes) {
            cleanup();

            // Clear chart canvas divs
            ['#position-chart', '#year-chart', '#category-chart'].forEach(function (sel) {
                var el = document.querySelector(containerSel + ' ' + sel);
                if (el) el.innerHTML = '';
            });

            if (!votes || votes.length === 0) {
                var noData = document.querySelector(containerSel + ' #no-votes-msg');
                if (noData) noData.style.display = 'block';
                return;
            }
            var noData = document.querySelector(containerSel + ' #no-votes-msg');
            if (noData) noData.style.display = 'none';

            var ndx = crossfilter(votes);

            function parseDate(d) {
                return d.date ? new Date(d.date) : new Date((d.year || 2000) + '-07-01');
            }

            var posDim   = ndx.dimension(function (d) { return d.position; });
            var dateDim  = ndx.dimension(parseDate);
            var catDim   = ndx.dimension(function (d) { return d.category || 'Uncategorized'; });
            var tableDim = ndx.dimension(function (d) { return d.year || 0; });

            var posGroup  = posDim.group();
            var yearGroup = dateDim.group(d3.timeYear);
            var catGroup  = catDim.group();

            var allDates  = votes.map(parseDate).sort(function (a, b) { return a - b; });
            var minDate   = allDates.length ? d3.timeYear.floor(allDates[0])                                : new Date('1946-01-01');
            var maxDate   = allDates.length ? d3.timeYear.offset(d3.timeYear.ceil(allDates[allDates.length - 1]), 1)
                                : new Date('2025-01-01');

            var containerEl = document.querySelector(containerSel);
            var panelW = containerEl ? containerEl.clientWidth : 700;

            // --- Position pie chart ---
            var posChart = dc.pieChart(containerSel + ' #position-chart', GROUP);
            posChart
                .width(220).height(220)
                .innerRadius(50)
                .dimension(posDim).group(posGroup)
                .colors(d3.scaleOrdinal()
                    .domain(['yes', 'no', 'abstain', 'absent'])
                    .range(['#27ae60', '#e74c3c', '#f39c12', '#95a7b5']))
                .colorAccessor(function (d) { return d.key; })
                .title(function (d) { return d.key + ': ' + d.value; });

            // --- Votes by year bar chart ---
            var yearChartEl = document.querySelector(containerSel + ' #year-chart');
            var yearW = yearChartEl
                ? Math.max(280, yearChartEl.parentElement.clientWidth - 260)
                : 480;

            var yearChart = dc.barChart(containerSel + ' #year-chart', GROUP);
            yearChart
                .width(yearW).height(180)
                .margins({ top: 10, right: 20, bottom: 30, left: 40 })
                .dimension(dateDim).group(yearGroup)
                .x(d3.scaleTime().domain([minDate, maxDate]))
                .xUnits(d3.timeYears)
                .round(d3.timeYear.round)
                .elasticY(true)
                .gap(1)
                .renderHorizontalGridLines(true)
                .brushOn(true);

            // --- Category row chart ---
            var uniqueCats = catGroup.all().length;
            var catH = Math.min(420, Math.max(80, uniqueCats * 24 + 40));
            var catChart = dc.rowChart(containerSel + ' #category-chart', GROUP);
            catChart
                .width(panelW > 40 ? panelW - 40 : 620).height(catH)
                .margins({ top: 5, right: 20, bottom: 25, left: 10 })
                .dimension(catDim).group(catGroup)
                .elasticX(true)
                .colors(d3.scaleOrdinal(d3.schemeSet2))
                .label(function (d) { return d.key; })
                .title(function (d) { return d.key + ': ' + d.value; })
                .gap(3);

            // --- Data count widget ---
            var countWidget = dc.dataCount(containerSel + ' #data-count', GROUP);
            countWidget
                .crossfilter(ndx)
                .groupAll(ndx.groupAll())
                .html({
                    some: '<strong>%filter-count</strong> of <strong>%total-count</strong> votes selected — <a href="#" class="votes-clear-link">clear filters</a>',
                    all:  'All <strong>%total-count</strong> votes'
                });

            // --- Data table ---
            var dataTable = dc.dataTable(containerSel + ' #data-table', GROUP);
            dataTable
                .dimension(tableDim)
                .size(50)
                .columns([
                    { label: 'Year',       format: function (d) { return d.year || '—'; } },
                    { label: 'Resolution', format: function (d) { return d.resolution; } },
                    { label: 'Title',      format: function (d) { return d.title ? d.title.slice(0, 80) + (d.title.length > 80 ? '…' : '') : '—'; } },
                    { label: 'Position',   format: function (d) { return d.position; } },
                    { label: 'Tally (Y/N/A)', format: function (d) {
                        return d.yes_count != null
                            ? d.yes_count + ' / ' + d.no_count + ' / ' + d.abstain_count
                            : '—';
                    }}
                ])
                .sortBy(function (d) { return d.year || 0; })
                .order(d3.descending)
                .on('renderlet.html', function (chart) {
                    // Resolution → link
                    chart.selectAll('td.col1').each(function (d) {
                        d3.select(this).html(
                            '<a href="' + d.row.document_url + '">' + d.row.resolution + '</a>'
                        );
                    });
                    // Position → badge
                    chart.selectAll('td.col3').each(function (d) {
                        d3.select(this).html(
                            '<span class="pos-badge pos-' + d.row.position + '">' + d.row.position + '</span>'
                        );
                    });
                });

            _charts = [posChart, yearChart, catChart, countWidget, dataTable];
            dc.renderAll(GROUP);

            // Clear-filters link inside data count
            containerEl.addEventListener('click', function (e) {
                if (e.target && e.target.classList.contains('votes-clear-link')) {
                    e.preventDefault();
                    VoteCharts.resetAll();
                }
            });
        },

        resetAll: function () {
            dc.filterAll(GROUP);
            dc.renderAll(GROUP);
        }
    };
}());
