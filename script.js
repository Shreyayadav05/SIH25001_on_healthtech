let map, markers = {}, chart;

function fetchData(){
  fetch('/api/alerts')
  .then(res=>res.json())
  .then(data=>{
    const list = document.getElementById('alerts-list');
    list.innerHTML="";
    const levels={High:0,Medium:0,Low:0};

    data.villages.forEach(v=>{
      levels[v.level]++;
      const li=document.createElement('li');
      li.className="p-2 border rounded flex justify-between items-center";
      li.innerHTML=`<span><strong>${v.name}</strong> - ${v.disease_alert} (Active: ${v.active_cases})</span>
      <span class="font-bold ${v.level.toLowerCase()}">${v.level}</span>
      <button onclick="downloadReport('${v.name}')" class="ml-2 bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-700">PDF</button>`;
      list.appendChild(li);

      // Map markers
      if(!markers[v.name]){
        markers[v.name]=L.circleMarker([v.lat,v.lon],{radius:10,color:colorLevel(v.level)}).addTo(map)
        .bindPopup(markerPopup(v));
      } else{
        markers[v.name].setLatLng([v.lat,v.lon]).setStyle({color:colorLevel(v.level)})
        .bindPopup(markerPopup(v));
      }
    });

    updateChart(levels);
  });
}

function colorLevel(level){return level==="High"?'red':level==="Medium"?'orange':'green';}
function markerPopup(v){return `<strong>${v.name}</strong><br>Disease: ${v.disease_alert}<br>Active Cases: ${v.active_cases}<br>pH: ${v.water_ph}, Turbidity: ${v.turbidity}, Temp: ${v.temperature}°C, Humidity: ${v.humidity}%`;}

// Map setup
map=L.map('map').setView([26.1,91.7],8);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

// Chart setup
const ctx=document.getElementById('diseaseChart').getContext('2d');
chart=new Chart(ctx,{type:'bar',data:{labels:['High','Medium','Low'],datasets:[{label:'Villages',data:[0,0,0],backgroundColor:['#ff4d4f','#ffa500','#28a745']}]},options:{responsive:true}});

function updateChart(levels){
  chart.data.datasets[0].data=[levels.High,levels.Medium,levels.Low];
  chart.update();
}

// Download PDF
function downloadReport(village){window.location.href=`/download-report/${village}`;}

// Auto-update every 5 sec
setInterval(fetchData,5000);
fetchData();
