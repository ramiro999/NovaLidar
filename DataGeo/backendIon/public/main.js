const dropZone = document.getElementById('dropZone');
const CESIUM_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJkOWU0ZGMxMi0zOTk2LTQ5ZDgtYTcwMC05ZmEwMzkxNDM4NGUiLCJpZCI6MzA5OTEwLCJpYXQiOjE3NDkyMjE1MjZ9.-kfogF2voR2l6Y9WMMtlBGBm-P8Xh1LMTRXk9byIzIs'; // reemplaza con tu token de visualización

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.style.borderColor = "green";
});

dropZone.addEventListener('drop', async (e) => {
  e.preventDefault();
  dropZone.style.borderColor = "#aaa";
  const file = e.dataTransfer.files[0];
  if (!file || !file.name.endsWith('.las')) {
    alert('Solo se permiten archivos .las');
    return;
  }
  const formData = new FormData();
  formData.append('file', file);
  try {
    const response = await fetch('/upload', {
      method: 'POST',
      body: formData
    });
    const data = await response.json();
    if (!data.success) {
      alert("Error subiendo archivo al servidor");
      return;
    }
    alert("Archivo subido correctamente. Esperando procesamiento en Cesium Ion...");

    const assetId = data.assetId;
    const assetReady = await waitForAssetReady(assetId, CESIUM_TOKEN);
    if (!assetReady) {
      alert("Error: El asset no está listo para visualizarse.");
      return;
    }

    alert("¡Asset procesado! Mostrando en Cesium...");

    Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJkOWU0ZGMxMi0zOTk2LTQ5ZDgtYTcwMC05ZmEwMzkxNDM4NGUiLCJpZCI6MzA5OTEwLCJpYXQiOjE3NDkyMjE1MjZ9.-kfogF2voR2l6Y9WMMtlBGBm-P8Xh1LMTRXk9byIzIs';
    const viewer = new Cesium.Viewer('cesiumContainer', {
      terrainProvider: Cesium.createWorldTerrainProvider()
    });
    const tileset = await Cesium.Cesium3DTileset.fromIonAssetId(assetId);
    viewer.scene.primitives.add(tileset);
    viewer.zoomTo(tileset);

  } catch (err) {
    console.error(err);
    alert("Error cargando archivo o visualizando en Cesium.");
  }
});

async function waitForAssetReady(assetId, token) {
  const MAX_RETRIES = 20;
  const INTERVAL = 3000;
  for (let i = 0; i < MAX_RETRIES; i++) {
    const res = await fetch(`https://api.cesium.com/v1/assets/${assetId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const data = await res.json();
    console.log("Estado del asset:", data.status);
    if (data.status === "COMPLETE") return true;
    if (data.status === "FAILED") return false;
    await new Promise(resolve => setTimeout(resolve, INTERVAL));
  }
  return false;
}
