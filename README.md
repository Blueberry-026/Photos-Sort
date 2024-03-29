# Photos-Sort

Photos-Sort permet de trier / archiver un lot de photos en vrac et de préparer un upload vers [Panoramax](https://panoramax.openstreetmap.fr/#focus=map&map=10/45.7666/4.836), [KartaView](https://kartaview.org), [Mappilary](https://www.mapillary.com) ou autres ...
A partir d'un répertoire de photos en vrac :
* copie toutes les photos en les renommant au format `HHhMNmSS-FFFF.jpg` dans un répertoire 
d'archive `/AAAA-MM-JJ - HHhMN/` (l'heure contenue dans le nom du répertoire est l'heure de la première photo du lot)
* copie les photos en les renommant au format `HHhMNmSS-FFFF.jpg` dans le répertoire d'upload limité aux photos qui :
  - contiennent un EXIF correct
  - ont recu une géoloc GPS correcte
  - sont à plus de X mètres de la dernière photo
  - sont à plus de Y mètres du domicile
  
Ce répertoire pourra ensuite etre uploadé avec [KartaView upload](https://github.com/kartaview/upload-scripts) ou [Panoramax CLI Upload](https://gitlab.com/geovisio/cli)

Le programme génère aussi
* un GPX de la trace complète (nommé `FULL-AAAA-MM-JJ - HHhMN (commentaire).gpx`)
* un GPX de la trace filtrée donc sans les images en double ou trop proches du domicile (nommé `FILTERED-AAAA-MM-JJ - HHhMN (commentaire).gpx`)
* un rapport d'analyse (`Analyse-AAAA-MM-JJ - HHhMN (commentaire).csv`)

```
usage: sort.py [-h] [-r REPERTOIRE] [-c COMMENT] [-d DOMICILE] [-f FILTRAGE] [-nu] [-na] [-nx]

SORT.PY == Utilitaire de tri de photos : renomme les photos au format
'HHhMNmSS-FFFF.jpg' et les range dans les répertoires définis ARCHIVE et
UPLOAD. Dans le répertoire UPLOAD, les images trop proches du domicile ou trop
proche d'une photo précédente sont filtrées.

optional arguments:
  -h, --help            show this help message and exit
  -r REPERTOIRE, --repertoire REPERTOIRE
                        Répertoire contenant les photos à trier (exemple: -r '/home/xxx/repertoire')
  -c COMMENT, --comment COMMENT
                        Commentaire à ajouter au dossier (exemple: -c 'Sortie vélo')
  -d DOMICILE, --domicile DOMICILE
                        Distance à filtrer autour du domicle en metres (exemple: -d 200)
  -f FILTRAGE, --filtrage FILTRAGE
                        Distance minimale entre 2 photos en mètres (exemple: -f 5)
  -nu, --noupload       Ne copie pas les fichiers dans le répertoire UPLOAD (exemple: -nu)
  -na, --noarchive      Ne copie pas les fichiers dans le répertoire ARCHIVE (exemple: -na)
  -nx, --nogpx          Ne génère pas le fichier GPX (exemple: -nx)

Exemple: >python sort.py -r '/home/xxx/repertoire' -c 'comment' -d 250 -f 5
```
