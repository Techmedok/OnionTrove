async function fetchDataAndDisplayCharts() {
  try {
      const response = await fetch('../data');
      const data = await response.json();

      displayChart("chart1", data.categories, data.values[0], '#FF5733'); // Orange
      displayChart("chart2", data.categories, data.values[1], '#3498DB'); // Blue
      displayChart("chart3", data.categories, data.values[2], '#27AE60'); // Green
      displayChart("chart4", data.categories, data.values[3], '#F39C12'); // Yellow
  } catch (error) {
      console.error('Error fetching data:', error);
  }
}

function displayChart(containerId, categories, values, color) {
  const options = {
      series: [{
          name: 'Series 1',
          data: values,
      }],
      chart: {
          height: 350,
          type: 'area',
          foreColor: '#333',
          toolbar: {
              show: false,
          },
      },
      dataLabels: {
          enabled: false,
      },
      stroke: {
          curve: 'smooth',
          width: 3,
      },
      xaxis: {
          type: 'datetime',
          categories: categories.map(date => {
              const parts = date.split(' ');
              const [dd, mm, yyyy] = parts[0].split('-');
              const [hh, min] = parts[1].split(':');
              return new Date(`${mm}-${dd}-${yyyy} ${hh}:${min}`).toISOString();
          }),
      },
      tooltip: {
          enabled: true,
          x: {
              format: 'dd/MM/yy HH:mm',
          },
      },
      colors: [color], // Set the color for the series
  };

  new ApexCharts(document.querySelector(`#${containerId}`), options).render();
}

fetchDataAndDisplayCharts();