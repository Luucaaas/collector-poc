"""Tests unitaires du contrôle des coordonnées (RM-02) et de la dérivation du slug (RM-06)."""

import pytest

from catalog.contact import CONTACT_EMAIL, CONTACT_PHONE, contact_reasons
from catalog.slug import slugify


@pytest.mark.parametrize(
    "text",
    [
        "écrivez-moi à jean.dupont@example.com pour négocier",
        "contact: a+b@sous.domaine.example.fr",
        "JEAN@EXAMPLE.COM",
    ],
)
def test_emails_detectes(text: str) -> None:
    assert contact_reasons(text) == [CONTACT_EMAIL]


@pytest.mark.parametrize(
    "text",
    [
        "appelez le 06 12 34 56 78 le soir",
        "0612345678",
        "06.12.34.56.78",
        "06-12-34-56-78",
        "01 23 45 67 89",
        "+33 6 12 34 56 78",
        "+33612345678",
        "+33 (0)6 12 34 56 78",
        "0033 6 12 34 56 78",
        "+44 7911 123456",
        "+1 415 555 0132",
        "+32 470 12 34 56",
        "00 49 151 23456789",
        "tel0612345678",
        "(0)6 12 34 56 78",
        "06/12/34/56/78",
        "Mon numéro : 06 12 34 56 78.",
        "WhatsApp +33 7 98 76 54 32 svp",
        "06 1234 5678",
        "0 6 12 34 56 78",
        "0 6 1 2 3 4 5 6 7 8",
        "06.12 34-56 78",
        "06 12 34 5678",
        "0612 34 56 78",
        "06\u00a012\u00a034\u00a056\u00a078",
        "06\u202f12\u202f34\u202f56\u202f78",
        "06  12 34 56 78",
        "Kenner 1979 06 12 34 56 78",
        "appelez le 06 12 34 56 78 2 fois",
        "Ligne directe : 01 23 45 67 89.",
        "+33(0)612345678",
    ],
)
def test_telephones_detectes(text: str) -> None:
    assert contact_reasons(text) == [CONTACT_PHONE]


@pytest.mark.parametrize(
    "text",
    [
        "Boba Fett Kenner 1979",
        "Édité en 1979, réédité en 1983",
        "Prix 120,00 € frais de port 8,50 €",
        "Vendu 1 200 € à débattre",
        "Dimensions 30 x 20 x 10 cm, 450 g",
        "Référence SW-1234-5678 boîte d'origine",
        "Lot de 12 figurines, taille 42",
        "Date d'achat : 05/11/1999",
        "Code-barres 5010993456789",
        "Numéro de série 2024-11-03",
        "Note 4,5/5 sur 1 000 avis",
        "Publié le 05.11.2024 14h",
        "Plus de +12 000 000 exemplaires",
        "Le 01/02/2024 à 10h",
        "Série 00 1234 5678",
        "Vente du 05/11/2024 à 14:30, port 8,50 €",
        "Lot de 0612345 pièces",
        "Édition limitée 1995, 25 000 exemplaires numérotés",
        "Taille 42 - 44 EU",
        "Code EAN 3760123456789",
        "Tirage +50 000 exemplaires",
        "",
    ],
)
def test_faux_positifs_evites(text: str) -> None:
    assert contact_reasons(text) == []


def test_email_et_telephone_donnent_les_deux_motifs_dans_l_ordre() -> None:
    assert contact_reasons("06 12 34 56 78 ou a@b.fr") == [CONTACT_EMAIL, CONTACT_PHONE]


def test_telephone_en_chiffres_unicode_detecte() -> None:
    # Le second chiffre peut être un chiffre non ASCII reconnu par \d (ici ٦, six arabe-indien).
    assert contact_reasons("Appelez le 0٦12345678") == [CONTACT_PHONE]


def test_plusieurs_textes_et_valeurs_absentes() -> None:
    assert contact_reasons("Titre propre", None, "mon@mail.fr") == [CONTACT_EMAIL]
    assert contact_reasons(None) == []


def test_formes_obfusquees_hors_perimetre() -> None:
    assert contact_reasons("zéro six douze trente-quatre", "jean arobase example point com") == []
    assert contact_reasons("jean @ example.com") == []


@pytest.mark.parametrize(
    ("name", "slug"),
    [
        ("Figurines Star Wars", "figurines-star-wars"),
        ("Baskets", "baskets"),
        ("Café & Thé : édition spéciale", "cafe-the-edition-speciale"),
        ("  Jouets   des années 80  ", "jouets-des-annees-80"),
        ("BD / Comics", "bd-comics"),
        ("Œuvres d'art", "oeuvres-d-art"),
        ("!!", ""),
    ],
)
def test_slugify(name: str, slug: str) -> None:
    assert slugify(name) == slug
