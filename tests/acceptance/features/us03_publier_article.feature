# language: fr
@US-03 @EF-03 @EF-04
Fonctionnalité: US-03 Publier un article avec contrôle automatique
  En tant que vendeur,
  je veux publier un article dans l'une de mes boutiques et qu'il soit contrôlé automatiquement
  afin qu'il soit mis en vente sans attendre une validation humaine.

  Contexte:
    Étant donné la catégorie "Figurines" existe
    Et la boutique "Jouets des années 80" de "alice" existe

  @RM-01 @RM-03 @EF-01 @EF-23
  Scénario: Un article conforme est publié et annoncé
    Étant donné l'utilisateur "alice" authentifié
    Quand il publie dans la boutique "Jouets des années 80" un article conforme de la catégorie "Figurines" au prix de 120.00 € avec 8.00 € de frais de port
    Alors la réponse a le statut 201
    Et l'article retourné a le statut "PUBLISHED"
    Et exactement 1 événement "article.published" est émis pour cet article
    Et un visiteur non authentifié voit cet article dans le catalogue filtré sur la catégorie "Figurines"

  @RM-02 @RM-03 @EF-05
  Scénario: Un article contenant une adresse email est rejeté
    Étant donné l'utilisateur "alice" authentifié
    Quand il publie dans la boutique "Jouets des années 80" un article dont la description est "Figurine Boba Fett 1979, écrivez-moi à boba.fan@example.com"
    Alors la réponse a le statut 201
    Et l'article retourné a le statut "REJECTED"
    Et les motifs de rejet contiennent "CONTACT_EMAIL"
    Et aucun événement "article.published" n'est émis pour cet article
    Et un visiteur non authentifié ne voit pas cet article dans le catalogue

  @RM-02 @RM-03 @EF-05
  Plan du scénario: Un article contenant un numéro de téléphone est rejeté quel que soit son format
    Étant donné l'utilisateur "alice" authentifié
    Quand il publie dans la boutique "Jouets des années 80" un article dont la description est "Figurine Boba Fett 1979 en boîte, appelez le <telephone>"
    Alors l'article retourné a le statut "REJECTED"
    Et les motifs de rejet contiennent "CONTACT_PHONE"

    Exemples:
      | telephone          |
      | 06 12 34 56 78     |
      | +33 6 12 34 56 78  |
      | 06.12.34.56.78     |
      | 0612345678         |

  @RM-01 @ENF-07
  Plan du scénario: Un article invalide est refusé sans être enregistré
    Étant donné l'utilisateur "alice" authentifié
    Quand il publie dans la boutique "Jouets des années 80" un article conforme dont le champ "<champ>" vaut "<valeur>"
    Alors la réponse a le statut 422
    Et la boutique "Jouets des années 80" ne contient aucun article

    Exemples:
      | champ       | valeur                                 |
      | price       | 0                                      |
      | price       | -5.00                                  |
      | price       | 12.345                                 |
      | photo_urls  | []                                     |
      | title       | Bof                                    |
      | category_id | 00000000-0000-0000-0000-000000000000   |

  @ENF-03
  Scénario: Un vendeur ne peut pas publier dans la boutique d'un autre vendeur
    Étant donné la boutique "Vinyles de Bob" de "bob" existe
    Et l'utilisateur "alice" authentifié
    Quand il publie dans la boutique "Vinyles de Bob" un article conforme de la catégorie "Figurines" au prix de 50.00 € avec 5.00 € de frais de port
    Alors la réponse a le statut 403

  @ENF-02 @ENF-03
  Plan du scénario: Seul un vendeur authentifié peut publier un article
    Étant donné <acteur>
    Quand il publie dans la boutique "Jouets des années 80" un article conforme de la catégorie "Figurines" au prix de 50.00 € avec 5.00 € de frais de port
    Alors la réponse a le statut <statut>

    Exemples:
      | acteur                              | statut |
      | un visiteur non authentifié         | 401    |
      | l'utilisateur "chloe" authentifié   | 403    |
