/* votes_charts.js — dc.js + crossfilter voting analysis charts */
(function () {
    'use strict';

    var GROUP = 'uvotes';
    var _charts = [];

    /* Module-level refs for external filtering and re-rendering */
    var _catDim      = null;
    var _dateDim     = null;
    var _tableDim    = null;
    var _majDim      = null;
    var _majFilter   = null;
    var _catFilter   = null;
    var _ndx         = null;
    var _containerSel = null;
    var _iso3        = null;
    var _body        = null;
    var _yearFrom    = null;
    var _yearTo      = null;
    var _simCache    = {};

    function cleanup() {
        _charts.forEach(function (c) {
            try { dc.chartRegistry.deregister(c, GROUP); } catch (e) {}
        });
        _charts    = [];
        _catDim    = null;
        _dateDim   = null;
        _tableDim  = null;
        _majDim    = null;
        _majFilter = null;
        _catFilter = null;
        _ndx       = null;
        _body      = null;
        _yearFrom  = null;
        _yearTo    = null;
    }

    /* Determine the majority position based on vote tallies */
    function majorityPos(d) {
        var y = d.yes_count || 0, n = d.no_count || 0, a = d.abstain_count || 0;
        if (y === 0 && n === 0 && a === 0) return null;
        if (y >= n && y >= a) return 'yes';
        if (n >= y && n >= a) return 'no';
        return 'abstain';
    }

    /* Compute how this country voted relative to the majority */
    function towardMajority(mp, position) {
        if (position === 'absent' || mp === null) return null;
        if (position === mp) return 'agree';
        if (position === 'abstain') return 'abstain';
        return 'against';
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

        var svg = d3.select(el).append('svg').attr('width', W).attr('height', H);
        var g   = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        items.forEach(function (d, i) {
            var y = i * (barH + gap);
            var barW = Math.max(0, innerW * d.score);
            var label = d.name.length > 17 ? d.name.slice(0, 16) + '…' : d.name;
            g.append('a')
                .attr('href', d.iso3 ? '/country/' + d.iso3 + '/' : null)
                .style('text-decoration', 'none')
              .append('text')
                .attr('x', -5).attr('y', y + barH / 2)
                .attr('text-anchor', 'end').attr('dominant-baseline', 'middle')
                .attr('font-size', '0.73rem')
                .attr('fill', d.iso3 ? 'var(--un-blue, #1a6fa8)' : '#333')
                .text(label);
            g.append('rect')
                .attr('x', 0).attr('y', y)
                .attr('width', barW).attr('height', barH)
                .attr('fill', color).attr('rx', 2);
            g.append('text')
                .attr('x', barW + 4).attr('y', y + barH / 2)
                .attr('dominant-baseline', 'middle')
                .attr('font-size', '0.72rem').attr('fill', '#666')
                .text(Math.round(d.score * 100) + '%');
        });
    }

    function applySimilarity(data) {
        if (!_containerSel) return;
        renderSimBar(_containerSel + ' #similarity-high-chart', data.similar,    '#009edb');
        renderSimBar(_containerSel + ' #similarity-low-chart',  data.dissimilar, '#e67e22');
    }

    function fetchSimilarity() {
        if (!_iso3) return;
        var url = '/votes/api/' + _iso3 + '/similarity/';
        var params = [];
        if (_body)             params.push('body=' + _body);
        if (_yearFrom != null) { params.push('year_from=' + _yearFrom); params.push('year_to=' + _yearTo); }
        if (_catFilter)        params.push('category=' + encodeURIComponent(_catFilter));
        if (params.length) url += '?' + params.join('&');

        var cacheKey = _iso3 + ':' + (_body || '') + ':' + (_yearFrom || '') + ':' + (_yearTo || '') + ':' + (_catFilter || '');
        if (_simCache[cacheKey]) {
            applySimilarity(_simCache[cacheKey]);
            return;
        }
        ['#similarity-high-chart', '#similarity-low-chart'].forEach(function (s) {
            var el = document.querySelector(_containerSel + ' ' + s);
            if (el) el.innerHTML = '<p style="color:var(--muted);font-size:0.85rem;margin:0.5rem 0;">Loading…</p>';
        });
        fetch(url)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                _simCache[cacheKey] = data;
                applySimilarity(data);
            });
    }

    /* ── Year trend line chart ──────────────────────────────────────────────── */
    function renderSessionTrend(votes) {
        var el = document.querySelector(_containerSel + ' #session-trend-chart');
        if (!el) return;
        el.innerHTML = '';

        var byYear = {};
        votes.forEach(function (d) {
            var yr = d.year;
            if (!yr) return;
            if (!byYear[yr]) {
                byYear[yr] = { year: yr, yes: 0, no: 0, abstain: 0, total: 0 };
            }
            if (d.position === 'absent') return;
            byYear[yr].total++;
            if      (d.position === 'yes') byYear[yr].yes++;
            else if (d.position === 'no')  byYear[yr].no++;
            else                           byYear[yr].abstain++;
        });

        var data = Object.values(byYear)
            .filter(function (d) { return d.total >= 3; })
            .sort(function (a, b) { return a.year - b.year; })
            .map(function (d) { return {
                year:    d.year,
                yes:     d.total ? d.yes     / d.total * 100 : 0,
                no:      d.total ? d.no      / d.total * 100 : 0,
                abstain: d.total ? d.abstain / d.total * 100 : 0,
            }; });

        if (data.length < 2) {
            el.innerHTML = '<p style="color:var(--muted);font-size:0.85rem;margin:0.5rem 0;">Not enough data to show a trend.</p>';
            return;
        }

        var containerW = el.parentElement ? el.parentElement.clientWidth - 30 : 640;
        var W  = Math.max(320, Math.min(containerW, 860));
        var H  = 210;
        var m  = { top: 16, right: 24, bottom: 38, left: 44 };
        var iW = W - m.left - m.right;
        var iH = H - m.top  - m.bottom;

        var svg = d3.select(el).append('svg').attr('width', W).attr('height', H);
        var g   = svg.append('g').attr('transform', 'translate(' + m.left + ',' + m.top + ')');

        var x = d3.scaleLinear()
            .domain(d3.extent(data, function (d) { return d.year; }))
            .range([0, iW]);
        var y = d3.scaleLinear().domain([0, 100]).range([iH, 0]);

        g.append('g')
            .call(d3.axisLeft(y).tickSize(-iW).ticks(5).tickFormat(''))
            .call(function (ax) {
                ax.select('.domain').remove();
                ax.selectAll('line').style('stroke', '#e0e0e0').style('stroke-dasharray', '3,3');
            });
        g.append('g')
            .attr('transform', 'translate(0,' + iH + ')')
            .call(d3.axisBottom(x).ticks(Math.min(data.length, 12)).tickFormat(d3.format('d')))
            .selectAll('text').style('font-size', '0.72rem');
        g.append('g')
            .call(d3.axisLeft(y).ticks(5).tickFormat(function (d) { return d + '%'; }))
            .selectAll('text').style('font-size', '0.72rem');
        g.append('text')
            .attr('x', iW / 2).attr('y', iH + 34)
            .attr('text-anchor', 'middle').attr('font-size', '0.72rem').attr('fill', '#888')
            .text('Year');

        var SERIES = [
            { key: 'yes',     color: '#27ae60', label: 'Yes' },
            { key: 'no',      color: '#e74c3c', label: 'No' },
            { key: 'abstain', color: '#f39c12', label: 'Abstain' },
        ];
        var dotR = data.length > 20 ? 2 : 3;
        SERIES.forEach(function (s) {
            var lineFn = d3.line()
                .defined(function (d) { return d[s.key] != null; })
                .x(function (d) { return x(d.year); })
                .y(function (d) { return y(d[s.key]); })
                .curve(d3.curveMonotoneX);
            g.append('path').datum(data)
                .attr('fill', 'none').attr('stroke', s.color)
                .attr('stroke-width', 2).attr('d', lineFn);
            g.selectAll('.dot-' + s.key).data(data).enter()
                .append('circle')
                .attr('cx', function (d) { return x(d.year); })
                .attr('cy', function (d) { return y(d[s.key]); })
                .attr('r', dotR).attr('fill', s.color);
        });
        SERIES.forEach(function (s, i) {
            var lx = iW - 190 + i * 66;
            g.append('rect').attr('x', lx).attr('y', -13).attr('width', 14).attr('height', 4).attr('fill', s.color).attr('rx', 2);
            g.append('text').attr('x', lx + 17).attr('y', -9).attr('font-size', '0.72rem').attr('fill', '#555').text(s.label);
        });
    }

    /* ── Majority alignment donut chart (d3, not dc.js) ────────────────────── */
    function renderMajorityAlignment(votes) {
        var el = document.querySelector(_containerSel + ' #toward-majority-chart');
        if (!el) return;
        el.innerHTML = '';

        var counts = { agree: 0, against: 0, abstain: 0 };
        votes.forEach(function (d) {
            if (counts[d.toward_majority] !== undefined) counts[d.toward_majority]++;
        });

        var data = [
            { key: 'Agree',   value: counts.agree,   color: '#27ae60' },
            { key: 'Against', value: counts.against,  color: '#e74c3c' },
            { key: 'Abstain', value: counts.abstain,  color: '#f39c12' },
        ].filter(function (d) { return d.value > 0; });

        if (!data.length) return;

        var W = 220, H = 220, r = 90, ir = 50;
        var svg = d3.select(el).append('svg').attr('width', W).attr('height', H);
        var g   = svg.append('g').attr('transform', 'translate(' + W/2 + ',' + H/2 + ')');

        var pie  = d3.pie().value(function (d) { return d.value; }).sort(null);
        var labelArc = d3.arc().innerRadius(r - 28).outerRadius(r - 28);

        var total = d3.sum(data, function (x) { return x.value; });

        var slices = g.selectAll('g.slice').data(pie(data)).enter()
            .append('g').attr('class', 'slice')
            .style('cursor', 'pointer')
            .on('click', function (_, d) {
                var key = d.data.key.toLowerCase();
                if (_majFilter === key) {
                    _majFilter = null;
                    _majDim.filterAll();
                } else {
                    _majFilter = key;
                    _majDim.filter(key);
                }
                dc.redrawAll(GROUP);
                redrawExtras(false);
            });

        slices.append('path')
            .attr('d', function (d) {
                var key = d.data.key.toLowerCase();
                var active = _majFilter === null || _majFilter === key;
                var outerR = active ? r : r - 8;
                return d3.arc().innerRadius(ir).outerRadius(outerR)(d);
            })
            .attr('fill', function (d) { return d.data.color; })
            .attr('opacity', function (d) {
                return (_majFilter === null || _majFilter === d.data.key.toLowerCase()) ? 1 : 0.35;
            })
            .append('title')
            .text(function (d) { return d.data.key + ': ' + d.data.value; });

        slices.append('text')
            .attr('transform', function (d) { return 'translate(' + labelArc.centroid(d) + ')'; })
            .attr('text-anchor', 'middle')
            .attr('font-size', '0.7rem')
            .attr('fill', '#fff')
            .text(function (d) {
                var pct = Math.round(d.data.value / total * 100);
                return pct >= 8 ? d.data.key : '';
            });
    }

    /* Re-render charts that operate on filtered record sets */
    function redrawExtras(refetchSimilarity) {
        if (!_ndx || !_tableDim || !_containerSel) return;
        var filtered = _tableDim.top(Infinity);
        renderMajorityAlignment(filtered);
        renderSessionTrend(filtered);
        if (refetchSimilarity) fetchSimilarity();
    }


    window.VoteCharts = {

        init: function (containerSel, votes, iso3, body) {
            cleanup();
            _containerSel = containerSel;
            _iso3         = iso3;
            _body         = body || null;

            var containerEl = document.querySelector(containerSel);

            ['#position-chart', '#similarity-high-chart', '#similarity-low-chart'].forEach(function (sel) {
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

            votes.forEach(function (d) {
                d.toward_majority = towardMajority(majorityPos(d), d.position);
            });

            var ndx = crossfilter(votes);
            _ndx = ndx;

            function parseDate(d) {
                return d.date ? new Date(d.date) : new Date((d.year || 2000) + '-07-01');
            }

            /* Two date dimensions: one for external year filtering, one for the majority bar chart */
            var dateDim      = ndx.dimension(parseDate);
            var chartDateDim = ndx.dimension(parseDate);
            var catDim       = ndx.dimension(function (d) { return d.category || 'Uncategorized'; });
            var tableDim     = ndx.dimension(function (d) { return d.year || 0; });
            var majDim       = ndx.dimension(function (d) { return d.toward_majority; });

            _catDim   = catDim;
            _dateDim  = dateDim;
            _tableDim = tableDim;
            _majDim   = majDim;

            /* ── Position pie chart ───────────────────────────────────── */
            var posDim   = ndx.dimension(function (d) { return d.position; });
            var posGroup = posDim.group();
            var posChart = dc.pieChart(containerSel + ' #position-chart', GROUP);
            posChart
                .width(220).height(220)
                .innerRadius(50)
                .dimension(posDim).group(posGroup)
                .colors(d3.scaleOrdinal()
                    .domain(['yes', 'no', 'abstain', 'absent', 'non_voting'])
                    .range(['#27ae60', '#e74c3c', '#f39c12', '#95a7b5', '#c8d6de']))
                .colorAccessor(function (d) { return d.key; })
                .title(function (d) { return d.key + ': ' + d.value; });

            posChart.on('filtered', function () { redrawExtras(false); });

            /* ── Voting records toward majority stacked bar ───────────── */
            var allDates = votes.map(parseDate).sort(function (a, b) { return a - b; });
            var minDate  = allDates.length ? d3.timeYear.floor(allDates[0]) : new Date('1946-01-01');
            var maxDate  = allDates.length
                ? d3.timeYear.offset(d3.timeYear.ceil(allDates[allDates.length - 1]), 1)
                : new Date('2025-01-01');

            var yearChartEl = document.querySelector(containerSel + ' #toward-majority-year-chart');
            var yearW = yearChartEl
                ? Math.max(280, yearChartEl.parentElement.clientWidth - 40)
                : 480;

            function makeYearGroup(pred) {
                return chartDateDim.group(d3.timeYear).reduce(
                    function (p, v) { return p + (pred(v) ? 1 : 0); },
                    function (p, v) { return p - (pred(v) ? 1 : 0); },
                    function () { return 0; }
                );
            }
            var agreeYG   = makeYearGroup(function (d) { return d.toward_majority === 'agree'; });
            var againstYG = makeYearGroup(function (d) { return d.toward_majority === 'against'; });
            var abstainYG = makeYearGroup(function (d) { return d.toward_majority === 'abstain'; });

            var majYearChart = dc.barChart(containerSel + ' #toward-majority-year-chart', GROUP);
            majYearChart
                .width(yearW).height(180)
                .margins({ top: 10, right: 20, bottom: 30, left: 40 })
                .x(d3.scaleTime().domain([minDate, maxDate]))
                .xUnits(d3.timeYears)
                .round(d3.timeYear.round)
                .elasticY(true)
                .gap(1)
                .renderHorizontalGridLines(true)
                .brushOn(false)
                .dimension(chartDateDim)
                .group(agreeYG,   'Agree')
                .stack(againstYG, 'Against')
                .stack(abstainYG, 'Abstain')
                .valueAccessor(function (d) { return d.value; })
                .ordinalColors(['#27ae60', '#e74c3c', '#f39c12'])
                .legend(dc.legend().x(yearW - 110).y(6).itemHeight(12).gap(5));

            /* ── Data count widget ───────────────────────────────────── */
            var countWidget = dc.dataCount(containerSel + ' #data-count', GROUP);
            countWidget
                .crossfilter(ndx)
                .groupAll(ndx.groupAll())
                .html({
                    some: '<strong>%filter-count</strong> of <strong>%total-count</strong> votes selected — <a href="#" class="votes-clear-link">clear filters</a>',
                    all:  'All <strong>%total-count</strong> votes'
                });

            /* ── Data table ──────────────────────────────────────────── */
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

            function resolutionLink(d) {
                return d.resolution_url
                    ? '<a href="' + d.resolution_url + '">' + d.resolution + '</a>'
                    : (d.resolution || '—');
            }

            var dataTable = dc.dataTable(containerSel + ' #data-table', GROUP);
            dataTable
                .dimension(tableDim)
                .size(Infinity)
                .beginSlice(tableOffset)
                .endSlice(tableOffset + TABLE_PAGE_SIZE)
                .columns([
                    { label: 'Year',          format: function (d) { return d.year || '—'; } },
                    { label: 'Resolution',    format: resolutionLink },
                    { label: 'Title',         format: function (d) { return d.title ? d.title.slice(0, 80) + (d.title.length > 80 ? '…' : '') : '—'; } },
                    { label: 'Category',      format: function (d) { return d.category || '—'; } },
                    { label: 'Position',      format: function (d) { return d.position; } },
                    { label: 'Tally (Y/N/A)', format: function (d) {
                        return d.yes_count != null
                            ? d.yes_count + ' / ' + d.no_count + ' / ' + d.abstain_count
                            : '—';
                    }}
                ])
                .sortBy(function (d) { return d.year || 0; })
                .order(d3.descending)
                .on('renderlet.html', function (chart) {
                    chart.selectAll('td.col4').each(function (d) {
                        d3.select(this).html(
                            '<span class="pos-badge pos-' + d.row.position + '">' + d.row.position + '</span>'
                        );
                    });
                    updateTableNav();
                });

            _charts = [posChart, majYearChart, countWidget, dataTable];
            dc.renderAll(GROUP);

            /* Reset table offset on filter */
            [posChart, majYearChart].forEach(function (c) {
                c.on('filtered.tblreset', function () {
                    tableOffset = 0;
                    dataTable.beginSlice(0).endSlice(TABLE_PAGE_SIZE).redraw();
                });
            });

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

            containerEl.addEventListener('click', function (e) {
                if (e.target && e.target.classList.contains('votes-clear-link')) {
                    e.preventDefault();
                    tableOffset = 0;
                    VoteCharts.resetAll();
                }
            });

            /* Initial render of extras */
            renderMajorityAlignment(votes);
            renderSessionTrend(votes);
            fetchSimilarity();
        },

        filterYear: function (from, to) {
            _yearFrom = from;
            _yearTo   = to;
            if (!_dateDim) return;
            if (from != null && to != null) {
                _dateDim.filterRange([new Date(from + '-01-01'), new Date((to + 1) + '-01-01')]);
            } else {
                _dateDim.filterAll();
            }
            dc.redrawAll(GROUP);
            redrawExtras(true);
            document.dispatchEvent(new CustomEvent('wc:yearfilter', {
                detail: from != null ? { yearFrom: from, yearTo: to } : null
            }));
        },

        filterCategory: function (val) {
            if (!_catDim) return;
            _catFilter = val || null;
            if (val) _catDim.filter(val);
            else _catDim.filterAll();
            dc.redrawAll(GROUP);
            redrawExtras(true);
        },

        resetAll: function () {
            _yearFrom  = null;
            _yearTo    = null;
            _majFilter = null;
            _catFilter = null;
            if (_catDim)  _catDim.filterAll();
            if (_dateDim) _dateDim.filterAll();
            if (_majDim)  _majDim.filterAll();
            dc.filterAll(GROUP);
            dc.renderAll(GROUP);
            redrawExtras(true);
            document.dispatchEvent(new CustomEvent('wc:yearfilter', { detail: null }));
        }
    };
}());
