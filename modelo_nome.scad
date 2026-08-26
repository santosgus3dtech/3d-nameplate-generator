$fn = 80;

nome = "PADRAO";
largura = 80;
altura = 105;

espessura_base = 3;
altura_texto = 1.2;
tamanho_texto = 10;

translate([largura / 2, altura - 15, espessura_base])
linear_extrude(height = altura_texto)
text(
    nome,
    size = tamanho_texto,
    font = "Arial Black",
    halign = "center",
    valign = "center"
);