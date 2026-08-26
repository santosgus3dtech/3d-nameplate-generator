import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { FontLoader } from "three/addons/loaders/FontLoader.js";
import { TextGeometry } from "three/addons/geometries/TextGeometry.js";

const container = document.getElementById("canvas-container");

const nomeInput = document.getElementById("nome");
const qrInput = document.getElementById("qr");
const corPlacaInput = document.getElementById("cor_placa");
const corDetalheInput = document.getElementById("cor_detalhe");
const qrTamanhoInput = document.getElementById("qr_tamanho");
const qrValor = document.getElementById("qr_valor");

let scene, camera, renderer, controls;
let grupoModelo;
let fonte = null;

const ALTURA_PLACA = 105;
const ESPESSURA_BASE = 3;
const TAMANHO_TEXTO = 10;
const MARGEM_LATERAL_TEXTO = 30;

init();
carregarFonte();

function init() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x2b2f32);

    camera = new THREE.PerspectiveCamera(
        45,
        container.clientWidth / container.clientHeight,
        0.1,
        1000
    );

    camera.position.set(80, -130, 120);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;

    const luzAmbiente = new THREE.AmbientLight(0xffffff, 0.65);
    scene.add(luzAmbiente);

    const luzDirecional = new THREE.DirectionalLight(0xffffff, 0.9);
    luzDirecional.position.set(80, -80, 150);
    scene.add(luzDirecional);

    const grid = new THREE.GridHelper(220, 22);
    grid.rotation.x = Math.PI / 2;
    grid.position.z = -0.1;
    scene.add(grid);

    grupoModelo = new THREE.Group();
    scene.add(grupoModelo);

    window.addEventListener("resize", onResize);

    nomeInput.addEventListener("input", atualizarPreview);
    qrInput.addEventListener("input", atualizarPreview);
    corPlacaInput.addEventListener("input", atualizarPreview);
    corDetalheInput.addEventListener("input", atualizarPreview);
    qrTamanhoInput.addEventListener("input", atualizarPreview);

    animar();
}

function carregarFonte() {
    const loader = new FontLoader();

    loader.load(
        "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/fonts/helvetiker_bold.typeface.json",
        function (font) {
            fonte = font;
            atualizarPreview();
        }
    );
}

function calcularLarguraTexto(nome) {
    let largura = 0;

    for (const c of nome) {
        let fator;

        if (c === " ") fator = 0.38;
        else if ("ilI.,:;!|".includes(c)) fator = 0.34;
        else if ("mwMW".includes(c)) fator = 1.0;
        else if ("ABCDEFGHJKLMNOPQRSTUVWXYZ".includes(c)) fator = 0.82;
        else if ("0123456789".includes(c)) fator = 0.72;
        else fator = 0.66;

        largura += fator * TAMANHO_TEXTO;
    }

    return largura;
}

function calcularLarguraPlaca(nome, qrTamanho) {
    const larguraTexto = calcularLarguraTexto(nome);
    const larguraPorTexto = larguraTexto + MARGEM_LATERAL_TEXTO * 2;
    const larguraPorQr = qrTamanho + 32;

    return Math.max(80, larguraPorTexto, larguraPorQr);
}

function criarBaseArredondada(largura, altura, raio, espessura) {
    const shape = new THREE.Shape();

    shape.moveTo(raio, 0);
    shape.lineTo(largura - raio, 0);
    shape.quadraticCurveTo(largura, 0, largura, raio);
    shape.lineTo(largura, altura - raio);
    shape.quadraticCurveTo(largura, altura, largura - raio, altura);
    shape.lineTo(raio, altura);
    shape.quadraticCurveTo(0, altura, 0, altura - raio);
    shape.lineTo(0, raio);
    shape.quadraticCurveTo(0, 0, raio, 0);

    const geometry = new THREE.ExtrudeGeometry(shape, {
        depth: espessura,
        bevelEnabled: false
    });

    geometry.center();

    return geometry;
}

function criarQrFake(qrTamanho, cor) {
    const grupo = new THREE.Group();

    const modulos = 25;
    const modulo = qrTamanho / modulos;

    const material = new THREE.MeshStandardMaterial({
        color: new THREE.Color(cor),
        roughness: 0.55
    });

    for (let y = 0; y < modulos; y++) {
        for (let x = 0; x < modulos; x++) {
            const borda = x < 2 || y < 2 || x > modulos - 3 || y > modulos - 3;

            let ativo = false;

            if (!borda) {
                ativo =
                    ((x * 7 + y * 11) % 5 === 0) ||
                    ((x + y) % 7 === 0);
            }

            if (ativo || marcadorQr(x, y, modulos)) {
                const geo = new THREE.BoxGeometry(modulo, modulo, 1);
                const bloco = new THREE.Mesh(geo, material);

                bloco.position.x = x * modulo - qrTamanho / 2 + modulo / 2;
                bloco.position.y = y * modulo - qrTamanho / 2 + modulo / 2;
                bloco.position.z = ESPESSURA_BASE / 2 + 0.5;

                grupo.add(bloco);
            }
        }
    }

    return grupo;
}

function marcadorQr(x, y, n) {
    return marcador(x, y, 2, 2) ||
           marcador(x, y, n - 9, 2) ||
           marcador(x, y, 2, n - 9);
}

function marcador(x, y, ox, oy) {
    const dentro = x >= ox && x < ox + 7 && y >= oy && y < oy + 7;
    if (!dentro) return false;

    const lx = x - ox;
    const ly = y - oy;

    return (
        lx === 0 || lx === 6 ||
        ly === 0 || ly === 6 ||
        (lx >= 2 && lx <= 4 && ly >= 2 && ly <= 4)
    );
}

function atualizarPreview() {
    if (!fonte) return;

    while (grupoModelo.children.length > 0) {
        const obj = grupoModelo.children[0];
        grupoModelo.remove(obj);
    }

    const nome = nomeInput.value || "Imagine3D";
    const corPlaca = corPlacaInput.value;
    const corDetalhe = corDetalheInput.value;
    const qrTamanho = Number(qrTamanhoInput.value);

    qrValor.textContent = `${qrTamanho} mm`;

    const largura = calcularLarguraPlaca(nome, qrTamanho);

    const materialPlaca = new THREE.MeshStandardMaterial({
        color: new THREE.Color(corPlaca),
        roughness: 0.5
    });

    const baseGeo = criarBaseArredondada(largura, ALTURA_PLACA, 7, ESPESSURA_BASE);
    const base = new THREE.Mesh(baseGeo, materialPlaca);
    base.rotation.x = 0;
    grupoModelo.add(base);

    const textoGeo = new TextGeometry(nome, {
        font: fonte,
        size: TAMANHO_TEXTO,
        height: 1.2,
        curveSegments: 8,
        bevelEnabled: false
    });

    textoGeo.computeBoundingBox();

    const textoWidth = textoGeo.boundingBox.max.x - textoGeo.boundingBox.min.x;

    const materialDetalhe = new THREE.MeshStandardMaterial({
        color: new THREE.Color(corDetalhe),
        roughness: 0.55
    });

    const textoMesh = new THREE.Mesh(textoGeo, materialDetalhe);

    textoMesh.position.x = -textoWidth / 2;
    textoMesh.position.y = ALTURA_PLACA / 2 - 20;
    textoMesh.position.z = ESPESSURA_BASE / 2;

    grupoModelo.add(textoMesh);

    const qr = criarQrFake(qrTamanho, corDetalhe);

    qr.position.x = 0;
    qr.position.y = -ALTURA_PLACA / 2 + 16 + qrTamanho / 2;
    qr.position.z = 0;

    grupoModelo.add(qr);

    controls.target.set(0, 0, 0);
    controls.update();
}

function onResize() {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

function animar() {
    requestAnimationFrame(animar);
    controls.update();
    renderer.render(scene, camera);
}