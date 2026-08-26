$fn = 80;

largura = 80;
altura = 105;
espessura_base = 3;
raio_canto = 7;

module retangulo_arredondado_2d(largura, altura, raio) {
    translate([raio, raio])
    offset(r = raio)
    square([largura - 2 * raio, altura - 2 * raio]);
}

linear_extrude(height = espessura_base)
retangulo_arredondado_2d(largura, altura, raio_canto);