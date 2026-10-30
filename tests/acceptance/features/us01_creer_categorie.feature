# language: fr
@US-01 @EF-27
Fonctionnalité: US-01 Créer une catégorie
  En tant qu'administrateur,
  je veux créer une catégorie d'objets de collection
  afin que les vendeurs y classent leurs articles et que les acheteurs s'y abonnent.

  Scénario: L'admin crée une catégorie visible publiquement
    Étant donné l'utilisateur "admin" authentifié
    Quand il crée la catégorie "Figurines Star Wars"
    Alors la réponse a le statut 201
    Et la catégorie retournée a le slug "figurines-star-wars"
    Et un visiteur non authentifié voit la catégorie "Figurines Star Wars" dans la liste des catégories

  @RM-06
  Scénario: Le nom d'une catégorie est unique sans tenir compte de la casse
    Étant donné la catégorie "Baskets" existe
    Et l'utilisateur "admin" authentifié
    Quand il crée la catégorie "baskets"
    Alors la réponse a le statut 409

  @RM-06
  Scénario: Un nom de catégorie trop court est refusé
    Étant donné l'utilisateur "admin" authentifié
    Quand il crée la catégorie "B"
    Alors la réponse a le statut 422
    Et la catégorie "B" n'existe pas

  @ENF-02
  Plan du scénario: Une requête sans jeton valide est refusée
    Étant donné <acteur>
    Quand il crée la catégorie "Vinyles"
    Alors la réponse a le statut 401
    Et la catégorie "Vinyles" n'existe pas

    Exemples:
      | acteur                                                    |
      | un visiteur non authentifié                               |
      | l'utilisateur "admin" avec un jeton expiré                |
      | l'utilisateur "admin" avec un jeton à signature falsifiée |

  @ENF-03
  Scénario: Un vendeur ne peut pas créer de catégorie
    Étant donné l'utilisateur "bob" authentifié
    Quand il crée la catégorie "Vinyles"
    Alors la réponse a le statut 403
