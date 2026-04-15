var canvas1 = document.getElementById('stage1');
var canvas2 = document.getElementById('stage2');
var canvas3 = document.getElementById('stage3');
const outputElement = document.getElementById('output_csv');

async function getCsvGraph() {
  var date = new Date();    // Dateオブジェクトを作成
  var a = date.getTime();   // UNIXタイムスタンプを取得する (ミリ秒単位)
  var curr_time = Math.floor( a / 1000 );  // UNIXタイムスタンプを取得する (秒単位)
  var tt = curr_time - 3600*24   // 24時間前
  const res = await fetch(`https://airoco.necolico.jp/data-api/day-csv?id=CgETViZ2&subscription-key=6b8aa7133ece423c836c38af01c59880&startDate=${tt}`);
  console.log("aaa");
  const raw_data = await res.text();
  console.log(raw_data);
  const data = convertArray(raw_data);
  for (var row of data){
    row[3] -= curr_time;
  }

  co2data = [];
  tempdata = [];
  RHdata = [];
  for (var row of data){
    co2data.push({x: row[3], y:row[0]});
    tempdata.push({x: row[3], y:row[1]});
    RHdata.push({x: row[3], y:row[2]});
  }

  var co2Chart = drawGraph(canvas1, co2data, 'CO2 density [ppm]');
  var tempChart = drawGraph(canvas2, tempdata, 'Temperature [deg]');
  var RHChart = drawGraph(canvas3, RHdata, 'Relative humidity [%]');
};

function drawGraph(canv, data, ylabel) {
  var chart = new Chart(canv, {
    type: 'scatter',
    data: {
      datasets: [{
        showLine: true,
        data: data,
        borderColor: '#48f',
      }]
    },
    options: {
      elements: {
         point:{
          radius: 0
        },
      },
      plugins: {
        legend: {// 凡例の非表示
          display: false
        }
      },
      scales: {
        x: {
          type: 'linear',
          position: 'bottom',
          title: {
            display: true,
            text: 'Time [s]',
            font: {
              size: 14,
            }
          }
        },
        y: {
          title: {
            display: true,
            text: ylabel,
            font: {
              size: 14,
            }
          }
        },
      },
    }
  });
  return chart;
}

function convertArray(data) {
  const dataArray = [];
  const dataString = data.split('\r\n');
  for (let i = 0; i < dataString.length; i++) {
    var data=dataString[i].split(',');
    if (data[1]=='Ｒ３ー４０１'){ 
      dataArray.push(data.slice(3,7).map(parseFloat));
    }
  }
  return dataArray;
}

getCsvGraph();
console.log("bbb");
