
function bindeTableHoverEffects(name, chart) {
  var selector = '#content-stats-type-counts-' + name + ' tr';
  $(selector).on('mouseover', function(event) {
    chart.focus(event.currentTarget.dataset.id);
  });

  $(selector).on('mouseout', function(event) {
    chart.focus();
  });

  $(selector).each(function( index ) {
      var data_id = this.dataset.id;
      d3.select(this).selectAll('td .legend-color')
                     .style('background-color', chart.color(data_id));
  });
}

function createPieChart(name, data) {
  var pie_chart = c3.generate({
    bindto: '#pie-chart-' + name,
    data: {
        json: [data],
        type : 'pie',
        legend: false,
        keys: {'value': Object.keys(data)},
    },
    size: {
        height: 360,
        width: 480
    },
    tooltip: {
        format: {
            value: function (value, ratio, id) {return value;}
        }
    }
  });

  pie_chart.legend.hide();
  bindeTableHoverEffects(name, pie_chart);
}

function createBarChart(name, data) {
  var bar_chart = c3.generate({
    bindto: '#bar-chart-' + name,
    data: {
        json: [data],
        type : 'bar',
        labels: true,
        legend: false,
        keys: {'value': Object.keys(data)}
    },
    tooltip: {
        grouped: false // Default true
    },
    axis: {
        x: {show:false}
    },
    grid: {
        y: {
            show: true
        }
    }
  });

  bar_chart.legend.hide();
  bindeTableHoverEffects(name, bar_chart);
}


$(function() {

  $('.statistic-wrapper').each(function(){
    var wrapper = $(this);
    var infos = wrapper.find('.content-stats-infos');
    var data = infos.data('counts');
    var name = infos.data('name');

    createPieChart(name, data);
    createBarChart(name, data);
  });

});
