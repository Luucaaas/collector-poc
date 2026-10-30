# language: fr
@US-05 @EF-12 @EF-15
Fonctionnalité: US-05 Centres d'intérêt, préférences et notifications de l'acheteur
  En tant qu'acheteur,
  je veux déclarer mes centres d'intérêt, suivre des articles et choisir les notifications que je reçois
  afin d'être prévenu des nouveaux articles et des baisses de prix qui m'intéressent.

  Contexte:
    Étant donné la catégorie "Figurines" existe
    Et la catégorie "Baskets" existe
    Et la boutique "Jouets des années 80" de "alice" existe

  Scénario: L'acheteur déclare ses centres d'intérêt
    Étant donné l'utilisateur "chloe" authentifié
    Quand il déclare les catégories "Baskets" et "Figurines" comme centres d'intérêt
    Alors la réponse a le statut 200
    Et ses centres d'intérêt sont "Baskets" et "Figurines"

  @EF-13 @RM-08 @ENF-14
  Scénario: L'acheteur est notifié d'un nouvel article correspondant à ses centres d'intérêt
    Étant donné "chloe" s'intéresse à la catégorie "Figurines"
    Et "chloe" a activé les notifications "NEW_ARTICLE"
    Et "alice" s'intéresse à la catégorie "Figurines"
    Quand "alice" publie l'article "Boba Fett Kenner 1979" dans la catégorie "Figurines" au prix de 120.00 €
    Alors en moins de 2 secondes "chloe" a une notification "NEW_ARTICLE" pour l'article "Boba Fett Kenner 1979" au prix de 120.00 €
    Et "alice" n'a aucune notification

  @EF-14 @RM-08
  Scénario: L'acheteur qui suit un article est notifié d'un changement de prix
    Étant donné "alice" a publié l'article "Boba Fett Kenner 1979" au prix de 120.00 €
    Et "chloe" suit l'article "Boba Fett Kenner 1979"
    Et "chloe" a activé les notifications "PRICE_CHANGED"
    Quand "alice" modifie le prix de l'article "Boba Fett Kenner 1979" à 95.00 €
    Alors en moins de 2 secondes "chloe" a une notification "PRICE_CHANGED" pour l'article "Boba Fett Kenner 1979" de 120.00 € à 95.00 €

  @EF-15 @RM-08
  Scénario: L'acheteur ne reçoit pas les types de notification qu'il a désactivés
    Étant donné "alice" a publié l'article "Boba Fett Kenner 1979" au prix de 120.00 €
    Et "chloe" suit l'article "Boba Fett Kenner 1979"
    Et "chloe" a désactivé les notifications "PRICE_CHANGED"
    Quand "alice" modifie le prix de l'article "Boba Fett Kenner 1979" à 95.00 €
    Alors après 2 secondes "chloe" n'a aucune notification

  @RM-09 @ENF-19
  Scénario: Un événement livré deux fois ne produit qu'une notification
    Étant donné "chloe" s'intéresse à la catégorie "Figurines"
    Et "chloe" a activé les notifications "NEW_ARTICLE"
    Quand le même événement "article.published" pour la catégorie "Figurines" est livré deux fois
    Alors après 2 secondes "chloe" a exactement 1 notification

  @ENF-02
  Scénario: Un visiteur non authentifié ne peut pas consulter de notifications
    Étant donné "chloe" a 1 notification
    Et un visiteur non authentifié
    Quand il consulte ses notifications
    Alors la réponse a le statut 401

  @ENF-03
  Scénario: Un acheteur ne voit que ses propres notifications
    Étant donné "chloe" a 1 notification
    Et l'utilisateur "alice" authentifié
    Quand il consulte ses notifications
    Alors la réponse a le statut 200
    Et aucune notification de "chloe" n'est retournée
