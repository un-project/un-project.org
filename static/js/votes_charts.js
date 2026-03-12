/* votes_charts.js — dc.js + crossfilter voting analysis charts */
(function () {
    'use strict';

    var GROUP = 'uvotes';
    var _charts = [];
    var _simCache = {}; /* iso3 → {similar, dissimilar} */

    function cleanup() {
        _charts.forEach(function (c) {
            try { dc.chartRegistry.deregister(c, GROUP); } catch (e) {}
        });
        _charts = [];
    }

    /* Compute the majority position for a vote record */
    function majorityPos(d) {
        var yc = d.yes_count, nc = d.no_count, ac = d.abstain_count;
        if (yc == null) return null;
        if (yc >= nc && yc >= ac) return 'yes';
        if (nc >= yc && nc >= ac) return 'no';
        return 'abstain';
    }

    /* Compute how this country voted relative to the majority */
    function towardMajority(d) {
        var mp = majorityPos(d);
        if (d.position === 'absent') return 'absent';
        if (mp === null) return d.position;
        if (d.position === mp) return 'agree';
        if (d.position === 'abstain') return 'abstain';
        return 'against';
    }

    /* Set innerHTML of the h3 inside the chart-box wrapping chartId */
    function setH3(containerSel, chartId, html) {
        var el = document.querySelector(containerSel + ' ' + chartId);
        if (el && el.parentElement) {
            var h3 = el.parentElement.querySelector('h3');
            if (h3) h3.innerHTML = html;
        }
    }

    /* Zero-filtering group wrapper (keeps row chart clean in majority mode) */
    function nonZero(group) {
        return {
            all: function () {
                return group.all().filter(function (d) { return d.value > 0; });
            }
        };
    }

    /* Render a simple d3 horizontal bar chart for similarity data */
    function renderSimBar(sel, items, color) {
        var el = document.querySelector(sel);
        if (!el) return;
        el.innerHTML = '';
        if (!items || items.length === 0) {
            el.innerHTML = '<p style="color:var(--muted);font-size:0.85rem;margin:0.5rem 0;">Not enough shared votes to compute.</p>';
            return;
        }

        var margin = { top: 4, right: 44, bottom: 4, left: 114 };
        var barH = 18, gap = 5;
        var containerW = el.parentElement ? el.parentElement.clientWidth - 30 : 260;
        var W = Math.max(200, Math.min(containerW, 420));
        var innerW = W - margin.left - margin.right;
        var H = items.length * (barH + gap) + margin.top + margin.bottom;

        var svg = d3.select(el).append('svg')
            .attr('width', W)
            .attr('height', H);

        var g = svg.append('g')
            .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        items.forEach(function (d, i) {
            var y = i * (barH + gap);
            var barW = Math.max(0, innerW * d.score);

            g.append('text')
                .attr('x', -5)
                .attr('y', y + barH / 2)
                .attr('text-anchor', 'end')
                .attr('dominant-baseline', 'middle')
                .attr('font-size', '0.73rem')
                .attr('fill', '#333')
                .text(d.name.length > 17 ? d.name.slice(0, 16) + '…' : d.name);

            g.append('rect')
                .attr('x', 0)
                .attr('y', y)
                .attr('width', barW)
                .attr('height', barH)
                .attr('fill', color)
                .attr('rx', 2);

            g.append('text')
                .attr('x', barW + 4)
                .attr('y', y + barH / 2)
                .attr('dominant-baseline', 'middle')
                .attr('font-size', '0.72rem')
                .attr('fill', '#666')
                .text(Math.round(d.score * 100) + '%');
        });
    }

    function applySimilarity(containerSel, data) {
        renderSimBar(containerSel + ' #similarity-high-chart', data.similar,    '#009edb');
        renderSimBar(containerSel + ' #similarity-low-chart',  data.dissimilar, '#e67e22');
    }

    window.VoteCharts = {

        init: function (containerSel, votes, mode, iso3) {
            cleanup();
            var majorityMode = (mode === 'majority');

            /* Clear chart canvas divs */
            ['#position-chart', '#year-chart', '#category-chart',
             '#similarity-high-chart', '#similarity-low-chart'].forEach(function (sel) {
                var el = document.querySelector(containerSel + ' ' + sel);
                if (el) el.innerHTML = '';
            });

            /* Show / hide similarity row */
            var simRow = document.querySelector(containerSel + ' #similarity-row');
            if (simRow) simRow.style.display = majorityMode ? 'flex' : 'none';

            if (!votes || votes.length === 0) {
                var noData = document.querySelector(containerSel + ' #no-votes-msg');
                if (noData) noData.style.display = 'block';
                return;
            }
            var noData = document.querySelector(containerSel + ' #no-votes-msg');
            if (noData) noData.style.display = 'none';

            /* Pre-compute majority fields on every record */
            votes.forEach(function (d) {
                d.majority_position = majorityPos(d);
                d.toward_majority   = towardMajority(d);
            });

            var ndx = crossfilter(votes);

            function parseDate(d) {
                return d.date ? new Date(d.date) : new Date((d.year || 2000) + '-07-01');
            }

            var dateDim  = ndx.dimension(parseDate);
            var catDim   = ndx.dimension(function (d) { return d.category || 'Uncategorized'; });
            var tableDim = ndx.dimension(function (d) { return d.year || 0; });

            var allDates = votes.map(parseDate).sort(function (a, b) { return a - b; });
            var minDate  = allDates.length ? d3.timeYear.floor(allDates[0])
                                           : new Date('1946-01-01');
            var maxDate  = allDates.length
                ? d3.timeYear.offset(d3.timeYear.ceil(allDates[allDates.length - 1]), 1)
                : new Date('2025-01-01');

            var containerEl = document.querySelector(containerSel);
            var panelW = containerEl ? containerEl.clientWidth : 700;
            var yearChartEl = document.querySelector(containerSel + ' #year-chart');
            var yearW = yearChartEl
                ? Math.max(280, yearChartEl.parentElement.clientWidth - 260)
                : 480;

            /* ── Position / Majority pie chart ───────────────────────────── */
            var posChart = dc.pieChart(containerSel + ' #position-chart', GROUP);

            if (majorityMode) {
                var majDim   = ndx.dimension(function (d) { return d.toward_majority; });
                var majGroup = majDim.group();
                posChart
                    .width(220).height(220)
                    .innerRadius(50)
                    .dimension(majDim).group(majGroup)
                    .colors(d3.scaleOrdinal()
                        .domain(['agree', 'against', 'abstain', 'absent'])
                        .range(['#27ae60', '#e74c3c', '#f39c12', '#95a7b5']))
                    .colorAccessor(function (d) { return d.key; })
                    .title(function (d) { return d.key + ': ' + d.value; });
                setH3(containerSel, '#position-chart', 'Vote position towards majority');
            } else {
                var posDim   = ndx.dimension(function (d) { return d.position; });
                var posGroup = posDim.group();
                posChart
                    .width(220).height(220)
                    .innerRadius(50)
                    .dimension(posDim).group(posGroup)
                    .colors(d3.scaleOrdinal()
                        .domain(['yes', 'no', 'abstain', 'absent'])
                        .range(['#27ae60', '#e74c3c', '#f39c12', '#95a7b5']))
                    .colorAccessor(function (d) { return d.key; })
                    .title(function (d) { return d.key + ': ' + d.value; });
                setH3(containerSel, '#position-chart', 'Vote position');
            }

            /* ── Year bar / stacked majority bar chart ────────────────────── */
            var yearChart = dc.barChart(containerSel + ' #year-chart', GROUP);
            yearChart
                .width(yearW).height(180)
                .margins({ top: 10, right: 20, bottom: 30, left: 40 })
                .x(d3.scaleTime().domain([minDate, maxDate]))
                .xUnits(d3.timeYears)
                .round(d3.timeYear.round)
                .elasticY(true)
                .gap(1)
                .renderHorizontalGridLines(true)
                .brushOn(true);

            if (majorityMode) {
                function makeYearGroup(pred) {
                    return dateDim.group(d3.timeYear).reduce(
                        function (p, v) { return p + (pred(v) ? 1 : 0); },
                        function (p, v) { return p - (pred(v) ? 1 : 0); },
                        function () { return 0; }
                    );
                }
                var agreeYG   = makeYearGroup(function (d) { return d.toward_majority === 'agree'; });
                var againstYG = makeYearGroup(function (d) { return d.toward_majority === 'against'; });
                var abstainYG = makeYearGroup(function (d) { return d.toward_majority === 'abstain'; });

                yearChart
                    .dimension(dateDim)
                    .group(agreeYG,   'Agree')
                    .stack(againstYG, 'Against')
                    .stack(abstainYG, 'Abstain')
                    .valueAccessor(function (d) { return d.value; })
                    .ordinalColors(['#27ae60', '#e74c3c', '#f39c12'])
                    .legend(dc.legend().x(yearW - 110).y(6).itemHeight(12).gap(5));
                setH3(containerSel, '#year-chart',
                    'Voting records toward majority <small style="font-size:0.72rem;font-weight:400;text-transform:none;">(drag to filter)</small>');
            } else {
                var yearGroup = dateDim.group(d3.timeYear);
                yearChart
                    .dimension(dateDim)
                    .group(yearGroup);
                setH3(containerSel, '#year-chart',
                    'Votes by year <small style="font-size:0.72rem;font-weight:400;text-transform:none;">(drag to filter)</small>');
            }

            /* ── Category row chart ──────────────────────────────────────── */
            var rawCatGroup, displayCatGroup, catH3text;
            if (majorityMode) {
                rawCatGroup = catDim.group().reduce(
                    function (p, v) { return p + (v.toward_majority === 'against' ? 1 : 0); },
                    function (p, v) { return p - (v.toward_majority === 'against' ? 1 : 0); },
                    function () { return 0; }
                );
                displayCatGroup = nonZero(rawCatGroup);
                catH3text = 'Disagreements by category';
            } else {
                rawCatGroup     = catDim.group();
                displayCatGroup = rawCatGroup;
                catH3text       = 'By category';
            }

            var uniqueCats = majorityMode
                ? rawCatGroup.all().filter(function (d) { return d.value > 0; }).length
                : rawCatGroup.all().length;
            var catH = Math.min(420, Math.max(80, uniqueCats * 24 + 40));

            var catChart = dc.rowChart(containerSel + ' #category-chart', GROUP);
            catChart
                .width(panelW > 40 ? panelW - 40 : 620).height(catH)
                .margins({ top: 5, right: 20, bottom: 25, left: 10 })
                .dimension(catDim).group(displayCatGroup)
                .elasticX(true)
                .colors(d3.scaleOrdinal(d3.schemeSet2))
                .label(function (d) { return d.key; })
                .title(function (d) { return d.key + ': ' + d.value; })
                .gap(3);
            setH3(containerSel, '#category-chart', catH3text);

            /* ── Data count widget ───────────────────────────────────────── */
            var countWidget = dc.dataCount(containerSel + ' #data-count', GROUP);
            countWidget
                .crossfilter(ndx)
                .groupAll(ndx.groupAll())
                .html({
                    some: '<strong>%filter-count</strong> of <strong>%total-count</strong> votes selected — <a href="#" class="votes-clear-link">clear filters</a>',
                    all:  'All <strong>%total-count</strong> votes'
                });

            /* ── Data table with client-side pagination ──────────────────── */
            var TABLE_PAGE_SIZE = 25;
            var tableOffset = 0;
            var tableAll    = ndx.groupAll();
            var tableNavEl  = document.querySelector(containerSel + ' #table-nav');

            function updateTableNav() {
                if (!tableNavEl) return;
                var total = tableAll.value();
                var start = total === 0 ? 0 : tableOffset + 1;
                var end   = Math.min(tableOffset + TABLE_PAGE_SIZE, total);
                var html  = '<span>' + start + '–' + end + ' of ' + total + '</span>';
                if (tableOffset > 0) html += ' <a href="#" id="tbl-prev" style="color:var(--un-blue);">&laquo; Prev</a>';
                if (end < total)     html += ' <a href="#" id="tbl-next" style="color:var(--un-blue);">Next &raquo;</a>';
                tableNavEl.innerHTML = html;
            }

            var tableColumns = majorityMode
                ? [
                    { label: 'Year',         format: function (d) { return d.year || '—'; } },
                    { label: 'Resolution',   format: function (d) { return d.resolution; } },
                    { label: 'Title',        format: function (d) { return d.title ? d.title.slice(0, 70) + (d.title.length > 70 ? '…' : '') : '—'; } },
                    { label: 'Position',     format: function (d) { return d.position; } },
                    { label: 'vs. Majority', format: function (d) {
                        return d.toward_majority + (d.majority_position ? ' (' + d.majority_position + ')' : '');
                    }}
                  ]
                : [
                    { label: 'Year',            format: function (d) { return d.year || '—'; } },
                    { label: 'Resolution',      format: function (d) { return d.resolution; } },
                    { label: 'Title',           format: function (d) { return d.title ? d.title.slice(0, 80) + (d.title.length > 80 ? '…' : '') : '—'; } },
                    { label: 'Position',        format: function (d) { return d.position; } },
                    { label: 'Tally (Y/N/A)',   format: function (d) {
                        return d.yes_count != null
                            ? d.yes_count + ' / ' + d.no_count + ' / ' + d.abstain_count
                            : '—';
                    }}
                  ];

            var dataTable = dc.dataTable(containerSel + ' #data-table', GROUP);
            dataTable
                .dimension(tableDim)
                .size(Infinity)
                .beginSlice(tableOffset)
                .endSlice(tableOffset + TABLE_PAGE_SIZE)
                .columns(tableColumns)
                .sortBy(function (d) { return d.year || 0; })
                .order(d3.descending)
                .on('renderlet.html', function (chart) {
                    /* Resolution → link (col1) */
                    chart.selectAll('td.col1').each(function (d) {
                        d3.select(this).html(
                            '<a href="' + d.row.document_url + '">' + d.row.resolution + '</a>'
                        );
                    });
                    /* Position → badge (col3) */
                    chart.selectAll('td.col3').each(function (d) {
                        d3.select(this).html(
                            '<span class="pos-badge pos-' + d.row.position + '">' + d.row.position + '</span>'
                        );
                    });
                    /* vs. Majority → badge (col4, majority mode only) */
                    if (majorityMode) {
                        chart.selectAll('td.col4').each(function (d) {
                            var tm    = d.row.toward_majority;
                            var color = tm === 'agree'   ? '#27ae60'
                                      : tm === 'against' ? '#e74c3c'
                                      : tm === 'abstain' ? '#f39c12'
                                      : '#95a7b5';
                            var mp = d.row.majority_position ? ' (' + d.row.majority_position + ')' : '';
                            d3.select(this).html(
                                '<span class="pos-badge" style="background:' + color + '">' + tm + mp + '</span>'
                            );
                        });
                    }
                    updateTableNav();
                });

            _charts = [posChart, yearChart, catChart, countWidget, dataTable];
            dc.renderAll(GROUP);

            /* Reset table page offset when any filter changes */
            dc.chartRegistry.list(GROUP).forEach(function (c) {
                if (c !== dataTable) {
                    c.on('filtered.tblreset', function () {
                        tableOffset = 0;
                        dataTable.beginSlice(0).endSlice(TABLE_PAGE_SIZE).redraw();
                    });
                }
            });

            /* Table prev/next navigation */
            if (tableNavEl) {
                tableNavEl.addEventListener('click', function (e) {
                    var el = e.target.closest('#tbl-prev, #tbl-next');
                    if (!el) return;
                    e.preventDefault();
                    if (el.id === 'tbl-prev') tableOffset = Math.max(0, tableOffset - TABLE_PAGE_SIZE);
                    if (el.id === 'tbl-next') tableOffset += TABLE_PAGE_SIZE;
                    dataTable.beginSlice(tableOffset).endSlice(tableOffset + TABLE_PAGE_SIZE).redraw();
                });
            }

            /* Clear-filters link */
            containerEl.addEventListener('click', function (e) {
                if (e.target && e.target.classList.contains('votes-clear-link')) {
                    e.preventDefault();
                    tableOffset = 0;
                    VoteCharts.resetAll();
                }
            });

            /* ── Similarity charts (majority mode only) ──────────────────── */
            if (majorityMode && iso3) {
                if (_simCache[iso3]) {
                    applySimilarity(containerSel, _simCache[iso3]);
                } else {
                    /* Show loading placeholder */
                    ['#similarity-high-chart', '#similarity-low-chart'].forEach(function (s) {
                        var el = document.querySelector(containerSel + ' ' + s);
                        if (el) el.innerHTML = '<p style="color:var(--muted);font-size:0.85rem;margin:0.5rem 0;">Loading…</p>';
                    });
                    fetch('/votes/api/' + iso3 + '/similarity/')
                        .then(function (r) { return r.json(); })
                        .then(function (data) {
                            _simCache[iso3] = data;
                            /* Only paint if the similarity row is still visible */
                            var row = document.querySelector(containerSel + ' #similarity-row');
                            if (row && row.style.display !== 'none') {
                                applySimilarity(containerSel, data);
                            }
                        });
                }
            }
        },

        resetAll: function () {
            dc.filterAll(GROUP);
            dc.renderAll(GROUP);
        }
    };
}());
