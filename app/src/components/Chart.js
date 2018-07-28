import React, { Component } from 'react';
import { select } from 'd3-selection';
import { scaleLinear, scaleTime } from 'd3-scale';
import { extent, min, max } from 'd3-array';
import { axisLeft, axisBottom } from 'd3-axis';
import { timeYear } from 'd3-time';
import { line, area, curveBasis  } from 'd3-shape';
import './Chart.css';

class Chart extends Component {
  _drawChart() {
    this._margin = {top: 20, right: 20, bottom: 40, left: 40};
    this._svg = select(this._svgElem);
    const bbox = this._svgElem.getBoundingClientRect();
    this._width = bbox.width - (this._margin.left + this._margin.right);
    this._height = bbox.height - (this._margin.top + this._margin.bottom);
    this._root = this._svg.append('g')
      .attr("transform", "translate(" + this._margin.left + "," + this._margin.top + ")");
    this._makeScales();
    this._drawAxes();
    this._drawPaths();
  }

  _makeScales() {
    const stats = this.props.data.stats;
    stats.forEach(s => s.date = new Date(s.year, 0, 1));
    this._scaleX = scaleTime()
      .range([0, this._width])
      .domain(extent(stats, d => d.date));
    this._scaleY = scaleLinear()
      .range([this._height, 0])
      .domain([min(stats, d => d.quantiles[0]), max(stats, d => d.quantiles[4])]);
  }

  _drawAxes() {
    const xAxis = axisBottom(this._scaleX)
      .ticks(timeYear)
      .tickSizeInner(-this._height)
      .tickSizeOuter(0)
      .tickPadding(10);
    const yAxis = axisLeft(this._scaleY)
      .tickSizeInner(-this._width)
      .tickSizeOuter(0)
      .tickPadding(10);

    const axes = this._root.append('g');
    axes.append('g')
      .attr('class', 'axis')
      .attr('transform', 'translate(0,' + this._height + ')')
      .call(xAxis);
    axes.append('g')
      .attr('class', 'axis')
      .call(yAxis);
  }

  _drawPaths() {
    const upperOuterArea = area()
      .curve(curveBasis)
      .x (d => this._scaleX(d.date))
      .y0(d => this._scaleY(d.quantiles[4]))
      .y1(d => this._scaleY(d.quantiles[3]));

    const upperInnerArea = area()
      .curve(curveBasis)
      .x (d => this._scaleX(d.date))
      .y0(d => this._scaleY(d.quantiles[3]))
      .y1(d => this._scaleY(d.quantiles[2]));

    const medianLine = line()
      .curve(curveBasis)
      .x (d => this._scaleX(d.date))
      .y(d => this._scaleY(d.quantiles[2]));

    const lowerInnerArea = area()
      .curve(curveBasis)
      .x (d => this._scaleX(d.date))
      .y0(d => this._scaleY(d.quantiles[2]))
      .y1(d => this._scaleY(d.quantiles[1]));

    const lowerOuterArea = area()
      .curve(curveBasis)
      .x (d => this._scaleX(d.date))
      .y0(d => this._scaleY(d.quantiles[1]))
      .y1(d => this._scaleY(d.quantiles[0]));

    this._root.datum(this.props.data.stats);

    this._root.append('path')
      .attr('class', 'area upper outer')
      .attr('d', upperOuterArea);

    this._root.append('path')
      .attr('class', 'area lower outer')
      .attr('d', lowerOuterArea);

    this._root.append('path')
      .attr('class', 'area upper inner')
      .attr('d', upperInnerArea);

    this._root.append('path')
      .attr('class', 'area lower inner')
      .attr('d', lowerInnerArea);

    this._root.append('path')
      .attr('class', 'median-line')
      .attr('d', medianLine);
  }

  componentDidUpdate() {
    if (this.props.data) {
      this._drawChart();
    }
  }

  render() {
    return (
      <div className="chart" style={{ padding: 10 }}>
        <svg ref={svg => this._svgElem = svg} preserveAspectRatio="xMinYMin" />
      </div>
    );
  }
}

export default Chart;
