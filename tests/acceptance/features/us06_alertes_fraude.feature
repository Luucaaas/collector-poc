# language: fr
@US-06 @EF-24 @EF-26
Fonctionnalité: US-06 Consulter et traiter les alertes de fraude
  En tant qu'administrateur,
  je veux consulter les alertes produites par l'analyse anti-fraude et statuer sur chacune
  afin de repérer les prix anormaux et les vendeurs suspects avant qu'ils ne lèsent des acheteurs.

  Contexte:
    Étant donné la catégorie "Figurines" existe
    Et la boutique "Jouets des années 80" de "alice" existe
    Et le plafond de prix anti-fraude est de 10000.00 €

  @RM-07
  Scénario: Un prix supérieur au plafond déclenche une alerte
    Étant donné l'utilisateur "admin" authentifié
    Quand "alice" publie l'article "Stormtrooper prototype" dans la catégorie "Figurines" au prix de 15000.00 €
    Alors en moins de 2 secondes la liste des alertes consultée par l'admin contient une alerte "PRICE_ABOVE_CEILING" pour l'article "Stormtrooper prototype" du vendeur "alice"

  @RM-07
  Plan du scénario: Une hausse de prix brutale déclenche une alerte
    Étant donné "alice" a publié l'article "Boba Fett Kenner 1979" au prix de 100.00 €
    Quand "alice" modifie le prix de l'article "Boba Fett Kenner 1979" à <nouveau_prix> €
    Alors après 2 secondes le nombre d'alertes "PRICE_SPIKE" pour l'article "Boba Fett Kenner 1979" est <alertes>

    Exemples:
      | nouveau_prix | alertes |
      | 180.00       | 1       |
      | 140.00       | 0       |

  @RM-07
  Scénario: Des modifications de prix répétées signalent un vendeur suspect
    Étant donné "alice" a publié l'article "Boba Fett Kenner 1979" au prix de 100.00 €
    Et "alice" a modifié 3 fois le prix de l'article "Boba Fett Kenner 1979" dans les dernières 24 heures
    Quand "alice" modifie le prix de l'article "Boba Fett Kenner 1979" à 99.00 €
    Alors en moins de 2 secondes il existe une alerte "FREQUENT_PRICE_CHANGES" pour l'article "Boba Fett Kenner 1979"

  Plan du scénario: L'admin statue sur une alerte
    Étant donné une alerte au statut "OPEN" existe
    Et l'utilisateur "admin" authentifié
    Quand il passe l'alerte au statut "<statut>"
    Alors la réponse a le statut 200
    Et l'alerte a le statut "<statut>"

    Exemples:
      | statut    |
      | CONFIRMED |
      | DISMISSED |

  @RM-09
  Scénario: Un événement livré deux fois ne produit qu'une alerte
    Quand le même événement "article.published" au prix de 15000.00 € est livré deux fois
    Alors après 2 secondes il existe exactement 1 alerte "PRICE_ABOVE_CEILING" pour cet événement

  @ENF-02 @ENF-03
  Plan du scénario: Seul l'admin consulte les alertes
    Étant donné <acteur>
    Quand il consulte les alertes
    Alors la réponse a le statut <statut>

    Exemples:
      | acteur                              | statut |
      | un visiteur non authentifié         | 401    |
      | l'utilisateur "alice" authentifié   | 403    |
