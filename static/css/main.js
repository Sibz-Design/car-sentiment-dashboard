// Main JavaScript file for additional functionality
(() => {
    'use strict';

    // 🌐 Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // ⏳ Show loading animation
    window.showLoading = function (elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-danger" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Loading...</p>
                </div>
            `;
        }
    };

    // ❌ Show error message
    window.showError = function (elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <strong>Error:</strong> ${message}
                </div>
            `;
        }
    };

    // ✅ Show success message
    window.showSuccess = function (elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `
                <div class="alert alert-success" role="alert">
                    <strong>Success:</strong> ${message}
                </div>
            `;
        }
    };

    // 🔁 Auto-refresh utility
    window.enableAutoRefresh = function (callback, interval = 300000) {
        setInterval(callback, interval);
    };

    // 🐞 Debug logger
    window.logDebug = function (message, data = null) {
        console.log(`[DEBUG] ${message}`, data);
    };

    // 🔢 Format number with commas
    window.formatNumber = function (num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    };

    // ✂️ Truncate long text
    window.truncateText = function (text, maxLength = 100) {
        return text.length <= maxLength ? text : text.substring(0, maxLength) + '...';
    };

    // 🧠 Initialize Bootstrap tooltips
    document.addEventListener('DOMContentLoaded', () => {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));
    });
})();

const paginationStates = {};
// ...
paginationStates = {}; // Reset pagination states
function createGradient(ctx, colorStart, colorEnd) {
  const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
  gradient.addColorStop(0, colorStart);
  gradient.addColorStop(1, colorEnd);
  return gradient;
}

async function fetchAndDisplayData(max_videos = 10, max_comments = 50) {
  document.getElementById('loading').style.display = 'block';
  const commentsSection = document.getElementById('comments-section');
  commentsSection.innerHTML = '';

  try {
    const chartRes = await fetch(`/api/chart-data?max_videos=${max_videos}&max_comments=${max_comments}`);
    if (!chartRes.ok) throw new Error('Failed to fetch chart data');
    const chartData = await chartRes.json();

    if (pieChart) pieChart.destroy();
    if (barChart) barChart.destroy();

    const pieCtx = document.getElementById('pieChart').getContext('2d');
    const pieGradientColors = chartData.pie_chart.colors.map(color => {
      // Create subtle gradient from color to white for each slice
      const grad = pieCtx.createRadialGradient(100, 75, 10, 100, 75, 150);
      grad.addColorStop(0, color);
      grad.addColorStop(1, 'rgba(255,255,255,0.7)');
      return grad;
    });

    pieChart = new Chart(pieCtx, {
      type: 'doughnut',
      data: {
        labels: chartData.pie_chart.labels,
        datasets: [{
          data: chartData.pie_chart.values,
          backgroundColor: pieGradientColors,
          borderColor: '#fff',
          borderWidth: 2,
          hoverOffset: 30,
        }]
      },
      options: {
        plugins: { legend: { position: 'bottom', labels: { padding: 20, boxWidth: 18, font: { size: 14 } } } },
        cutout: '40%',
        animation: {
          animateRotate: true,
          animateScale: true
        },
        responsive: true,
        maintainAspectRatio: false
      }
    });

    const barCtx = document.getElementById('barChart').getContext('2d');
    const barGradient = createGradient(barCtx, '#d90429', '#660000');

    // Plugin for rounded corners on bars
    const roundBarPlugin = {
      id: 'roundedBar',
      afterDatasetsDraw(chart) {
        const ctx = chart.ctx;
        chart.getDatasetMeta(0).data.forEach(bar => {
          const radius = 8;
          const {x, y, base, width} = bar;
          ctx.save();
          ctx.fillStyle = barGradient;
          ctx.shadowColor = 'rgba(0,0,0,0.25)';
          ctx.shadowBlur = 6;
          ctx.shadowOffsetX = 2;
          ctx.shadowOffsetY = 2;

          ctx.beginPath();
          ctx.moveTo(x - width / 2, base);
          ctx.lineTo(x - width / 2, y + radius);
          ctx.quadraticCurveTo(x - width / 2, y, x - width / 2 + radius, y);
          ctx.lineTo(x + width / 2 - radius, y);
          ctx.quadraticCurveTo(x + width / 2, y, x + width / 2, y + radius);
          ctx.lineTo(x + width / 2, base);
          ctx.closePath();
          ctx.fill();
          ctx.restore();
        });
      }
    };

    barChart = new Chart(barCtx, {
      type: 'bar',
      data: {
        labels: chartData.bar_chart.labels,
        datasets: [{
          label: 'Comments per Day',
          data: chartData.bar_chart.values,
          backgroundColor: barGradient,
          borderRadius: 8,
          borderSkipped: false,
          hoverBackgroundColor: '#9e1212'
        }]
      },
      options: {
        scales: {
          x: {
            ticks: { maxRotation: 90, minRotation: 45, color: '#d90429', font: { weight: 'bold' } },
            grid: { display: false }
          },
          y: {
            beginAtZero: true,
            ticks: { color: '#d90429', font: { weight: 'bold' } },
            grid: { color: '#f0f0f0' }
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: { enabled: true }
        },
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 1000,
          easing: 'easeOutBounce'
        }
      },
      plugins: [roundBarPlugin]
    });

    // Continue with comments rendering...

  } catch (err) {
    console.error(err);
    document.getElementById('comments-section').innerHTML = '<p class="text-danger">Error loading comments or charts.</p>';
  } finally {
    document.getElementById('loading').style.display = 'none';
  }
}
new Chart(document.getElementById('lineChart').getContext('2d'), {
  type: 'line',
  data: {
    labels: labels,
    datasets: [
      {
        label: 'Positive',
        data: trendData.map(t => t.Positive),
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.4,
        fill: true
      },
      {
        label: 'Neutral',
        data: trendData.map(t => t.Neutral),
        borderColor: 'rgba(201, 203, 207, 1)',
        backgroundColor: 'rgba(201, 203, 207, 0.2)',
        tension: 0.4,
        fill: true
      },
      {
        label: 'Negative',
        data: trendData.map(t => t.Negative),
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.4,
        fill: true
      }
    ]
  },
  options: {
    responsive: true,
    plugins: {
      legend: {
        labels: {
          color: getComputedStyle(document.body).getPropertyValue('--text-color')
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          color: getComputedStyle(document.body).getPropertyValue('--text-color')
        }
      },
      x: {
        ticks: {
          display: false  // Hide labels but keep axis & grid
        },
        grid: {
          drawTicks: false
        }
      }
    }
  }
});
x: {
  ticks: {
    display: false  // Hide only the labels (titles), keep grid lines
  },
  grid: {
    drawTicks: false
  }
}
// Line Chart
new Chart(document.getElementById('lineChart').getContext('2d'), {
  type: 'line',
  data: {
    labels: labels,  // still used internally
    datasets: [
      {
        label: 'Positive',
        data: trendData.map(t => t.Positive),
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.4,
        fill: true
      },
      {
        label: 'Neutral',
        data: trendData.map(t => t.Neutral),
        borderColor: 'rgba(201, 203, 207, 1)',
        backgroundColor: 'rgba(201, 203, 207, 0.2)',
        tension: 0.4,
        fill: true
      },
      {
        label: 'Negative',
        data: trendData.map(t => t.Negative),
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        tension: 0.4,
        fill: true
      }
    ]
  },
  options: {
    responsive: true,
    plugins: {
      legend: {
        labels: {
          color: getComputedStyle(document.body).getPropertyValue('--text-color')
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          color: getComputedStyle(document.body).getPropertyValue('--text-color')
        }
      },
      x: {
        display: false  // 💥 Hides the video titles (X-axis labels)
      }
    }
  }
});
