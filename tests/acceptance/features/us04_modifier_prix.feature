# language: fr
@US-04 @EF-06
Fonctionnalité: US-04 Modifier le prix d'un article
  En tant que vendeur,
  je veux modifier le prix d'un de mes articles publiés
  afin d'ajuster mon offre au marché, tout en gardant l'historique des prix.

  Contexte:
    Étant donné la catégorie "Figurines" existe
    Et la boutique "Jouets des années 80" de "alice" existe
    Et "alice" a publié l'article "Boba Fett Kenner 1979" au prix de 120.00 €

  @RM-04 @EF-23 @ENF-08
  Scénario: Le vendeur baisse son prix, l'historique et l'événement sont produits
    Étant donné l'utilisateur "alice" authentifié
    Quand il modifie le prix de l'article "Boba Fett Kenner 1979" à 95.00 €
    Alors la réponse a le statut 200
    Et l'article "Boba Fett Kenner 1979" a le prix de 95.00 €
    Et l'historique des prix de l'article "Boba Fett Kenner 1979" contient une entrée de 120.00 € à 95.00 € attribuée à "alice"
    Et exactement 1 événement "article.price_changed" est émis pour cet article avec l'ancien prix 120.00 € et le nouveau prix 95.00 €

  @RM-04
  Scénario: Un prix identique ne crée ni historique ni événement
    Étant donné l'utilisateur "alice" authentifié
    Quand il modifie le prix de l'article "Boba Fett Kenner 1979" à 120.00 €
    Alors la réponse a le statut 200
    Et l'historique des prix de l'article "Boba Fett Kenner 1979" est vide
    Et aucun événement "article.price_changed" n'est émis pour cet article

  @RM-01 @ENF-07
  Plan du scénario: Un prix invalide est refusé et le prix reste inchangé
    Étant donné l'utilisateur "alice" authentifié
    Quand il modifie le prix de l'article "Boba Fett Kenner 1979" à <prix> €
    Alors la réponse a le statut 422
    Et l'article "Boba Fett Kenner 1979" a le prix de 120.00 €

    Exemples:
      | prix   |
      | 0      |
      | -10.00 |
      | 1.234  |

  @ENF-02 @ENF-03
  Plan du scénario: Seul le propriétaire de l'article peut modifier son prix
    Étant donné <acteur>
    Quand il modifie le prix de l'article "Boba Fett Kenner 1979" à 10.00 €
    Alors la réponse a le statut <statut>
    Et l'article "Boba Fett Kenner 1979" a le prix de 120.00 €

    Exemples:
      | acteur                            | statut |
      | un visiteur non authentifié       | 401    |
      | l'utilisateur "bob" authentifié   | 403    |

  @RM-04
  Scénario: Le prix d'un article rejeté ne peut pas être modifié
    Étant donné "alice" a un article rejeté "Figurine à négocier par téléphone"
    Et l'utilisateur "alice" authentifié
    Quand il modifie le prix de l'article "Figurine à négocier par téléphone" à 30.00 €
    Alors la réponse a le statut 409

  @ENF-08
  Scénario: L'historique des prix est restitué dans l'ordre chronologique
    Étant donné l'utilisateur "alice" authentifié
    Et il a modifié successivement le prix de l'article "Boba Fett Kenner 1979" à 110.00 €, 100.00 € puis 105.00 €
    Quand il consulte l'historique des prix de l'article "Boba Fett Kenner 1979"
    Alors la réponse a le statut 200
    Et l'historique contient dans l'ordre les entrées :
      | ancien_prix | nouveau_prix |
      | 120.00      | 110.00       |
      | 110.00      | 100.00       |
      | 100.00      | 105.00       |
