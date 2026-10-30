# language: fr
@US-02 @EF-02
Fonctionnalité: US-02 Créer une boutique
  En tant que vendeur,
  je veux créer une ou plusieurs boutiques virtuelles
  afin de regrouper mes articles par thème, en étant clairement identifié comme vendeur particulier.

  Scénario: Un vendeur crée une boutique de vendeur particulier
    Étant donné l'utilisateur "alice" authentifié
    Quand il crée la boutique "Jouets des années 80"
    Alors la réponse a le statut 201
    Et la boutique retournée appartient à "alice"
    Et la boutique retournée a le type de vendeur "INDIVIDUAL"

  Scénario: La page publique d'une boutique identifie un vendeur particulier
    Étant donné la boutique "Jouets des années 80" de "alice" existe
    Et un visiteur non authentifié
    Quand il consulte la boutique "Jouets des années 80"
    Alors la réponse a le statut 200
    Et la boutique retournée a le type de vendeur "INDIVIDUAL"

  Scénario: Un vendeur peut posséder plusieurs boutiques
    Étant donné la boutique "Jouets des années 80" de "alice" existe
    Et l'utilisateur "alice" authentifié
    Quand il crée la boutique "Posters dédicacés"
    Alors la réponse a le statut 201
    Et la liste de ses boutiques contient 2 boutiques

  @RM-05
  Scénario: Le nom d'une boutique est unique sur la plateforme sans tenir compte de la casse
    Étant donné la boutique "Jouets des années 80" de "alice" existe
    Et l'utilisateur "bob" authentifié
    Quand il crée la boutique "jouets des années 80"
    Alors la réponse a le statut 409

  @RM-02 @EF-05
  Plan du scénario: Une boutique ne peut pas afficher de coordonnées personnelles
    Étant donné l'utilisateur "alice" authentifié
    Quand il crée la boutique "Ma collection" avec la description "<description>"
    Alors la réponse a le statut 422
    Et le motif de refus est "CONTACT_INFO_FORBIDDEN"
    Et la boutique "Ma collection" n'existe pas

    Exemples:
      | description                                   |
      | Écrivez-moi à collector.fan@example.com       |
      | Appelez le 06 12 34 56 78 pour négocier       |

  @ENF-02 @ENF-03
  Plan du scénario: Seul un vendeur authentifié peut créer une boutique
    Étant donné <acteur>
    Quand il crée la boutique "Boutique interdite"
    Alors la réponse a le statut <statut>

    Exemples:
      | acteur                              | statut |
      | un visiteur non authentifié         | 401    |
      | l'utilisateur "chloe" authentifié   | 403    |
