const express = require("express");
const multer = require("multer");
const cors = require("cors");
const path = require("path");
const fs = require("fs");
const axios = require("axios");
const AWS = require("aws-sdk");

const app = express();
const port = 3000;

// Reemplaza con tu token de Cesium Ion
const CESIUM_ION_TOKEN =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJiMzcwNmZkYi00ZWFhLTQ5YjAtOTRlOS1lNTdjNDg5YzY1NjkiLCJpZCI6MzA5OTEwLCJpYXQiOjE3NDkyMjMzNDB9.U2AgQxnwAM7__j5sF0rq5Wrsi1G_JxvHk2_dvQYi8J8";

app.use(cors());
app.use(express.static(path.join(__dirname, "public")));

const upload = multer({ dest: "uploads/" });

app.post("/upload", upload.single("file"), async (req, res) => {
  const file = req.file;

  try {
    console.log("Archivo recibido:", file.originalname);

    // 1️⃣ Crear asset en Cesium Ion
    const assetResponse = await axios.post(
      "https://api.cesium.com/v1/assets",
      {
        name: file.originalname,
        description: "Subido desde app local",
        type: "3DTILES",
        options: {
          sourceType: "POINT_CLOUD", // Indicar que es un archivo LAS/LAZ
        },
      },
      {
        headers: {
          Authorization: `Bearer ${CESIUM_ION_TOKEN}`,
          "Content-Type": "application/json",
        },
      }
    );

    console.log("Asset creado:", assetResponse.data);

    const assetData = assetResponse.data;
    const {
      bucket,
      endpoint,
      prefix,
      accessKey,
      secretAccessKey,
      sessionToken,
    } = assetData.uploadLocation;

    // 2️⃣ Configurar S3 temporal
    const s3 = new AWS.S3({
      accessKeyId: accessKey,
      secretAccessKey: secretAccessKey,
      sessionToken: sessionToken,
      endpoint: endpoint,
      region: "us-east-1",
      signatureVersion: "v4",
    });

    // 3️⃣ Subir archivo a S3
    const fileStream = fs.createReadStream(file.path);
    await s3
      .upload({
        Bucket: bucket,
        Key: `${prefix}${file.originalname}`,
        Body: fileStream,
      })
      .promise();

    console.log("Archivo subido correctamente a S3");

    // 4️⃣ Marcar la subida como completa
    await axios.post(assetData.onComplete.url, assetData.onComplete.fields, {
      headers: {
        Authorization: `Bearer ${CESIUM_ION_TOKEN}`,
      },
    });

    console.log("Subida completa notificada a Cesium Ion");

    // 5️⃣ Responder al cliente
    res.json({ success: true, assetId: assetData.assetMetadata.id });
  } catch (error) {
    console.error(
      "❌ Error al crear asset:",
      error.response?.data || error.message
    );
    res
      .status(500)
      .json({ success: false, error: "Fallo al crear asset en Cesium" });
  }
});

app.listen(port, () => {
  console.log(`Servidor corriendo en http://localhost:${port}`);
});
