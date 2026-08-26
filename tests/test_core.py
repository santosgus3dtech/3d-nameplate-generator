from gerador_3mf import (
    calcular_largura_placa,
    escapar_scad_string,
    limpar_nome_arquivo,
    normalizar_cor,
)


def test_filename_cleanup_removes_windows_reserved_characters():
    assert limpar_nome_arquivo('Ana/QR: "VIP"') == "Ana_QR___VIP_"


def test_color_normalization_adds_alpha_and_keeps_fallbacks_safe():
    assert normalizar_cor("#123456", "#FFFFFFFF") == "#123456FF"
    assert normalizar_cor("ABCDEF", "#FFFFFFFF") == "#ABCDEFFF"
    assert normalizar_cor("#BAD", "#FFFFFFFF") == "#FFFFFFFF"


def test_plate_width_respects_text_and_qr_minimums():
    assert calcular_largura_placa("A", 42) >= 80
    assert calcular_largura_placa("A very long custom name", 42) > 80


def test_scad_string_escaping():
    assert escapar_scad_string('A "quote" path\\test') == 'A \\"quote\\" path\\\\test'
