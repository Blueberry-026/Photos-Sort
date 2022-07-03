# Photos-Sort

Photos-Sort permet de trier / archiver un lot de photos et de préparer un upload vers 
[KartaView](https://kartaview.org], [Mappilary][https://www.mapillary.com/] ou autres ...
A partir d'un répertoire de photos en vrac :
* copie toutes les photos en les renommant au format `HHhMNmSS-FFFF.jpg` dans un répertoire 
d'archive `/AAAA-MM-JJ - HHhMN/` (l'heure contenue dans le nom du répertoire et l'heure de la première photo du lot)
* copie les photos en les renommant au format `HHhMNmSS-FFFF.jpg` dans le répertoire d'upload limité au photos qui : 
sont à plus de X mètres de la dernière photosont à plus de X mètres du domicile
** contiennent un EXIF correct
** ont recu une géoloc GPS correcte
Ce répertoire pourra ensuite etre uploadé avec [KartaView upload][https://github.com/kartaview/upload-scripts]

Le programme génère aussi* un GPX de la trace complète (format "FULL-AAAA-MM-JJ - HHhMN (commentaire).gpx") et de la trace filtrée (format `FILTERED-AAAA-MM-JJ - HHhMN 
(commentaire).gpx`)* un rapport d'analyse (`Analyse-AAAA-MM-JJ - HHhMN (commentaire).csv`)

```
usage: sort.py [-h] [-r REPERTOIRE] [-c COMMENT] [-d DOMICILE] [-f FILTRAGE] [-nu NOUPLOAD] [-na NOARCHIVE] [-nx NOGPX]

SORT.PY == Utilitaire de tri de photos : renome les photos au format 'HHhMNmSS-FFFF.jpg' et les range dans les répertoires ARCHIVE et UPLOAD. Dans le répertoire UPLOAD, les images trop
proches du domicile ou trop proche d'une photo précédente sont filtrées.

options:
  -h, --help            show this help message and exit
  -r REPERTOIRE, --repertoire REPERTOIRE
                        Répertoire contenant les photos à trier (exemple: -r '/media/blueb/Datas/ImagesRues/_a trier_')
  -c COMMENT, --comment COMMENT
                        Commentaire à ajouter au dossier (exemple: -c 'Fourviere')
  -d DOMICILE, --domicile DOMICILE
                        Distance à filtrer autour du domicle en metres (exemple: -d 200)
  -f FILTRAGE, --filtrage FILTRAGE
                        Distance minimale entre 2 photos en metres (exemple: -f 5)
  -nu NOUPLOAD, --noupload NOUPLOAD
                        Ne copie pas les fichiers dans le repertoire UPLOAD (exemple: -nu 1)
  -na NOARCHIVE, --noarchive NOARCHIVE
                        Ne copie pas les fichiers dans le repertoire ARCHIVE (exemple: -na 1)
  -nx NOGPX, --nogpx NOGPX
                        Ne genere pas le fichier GPX (exemple: -nx 1)

Exemple: >Python3 sort.py -r '/media/blueb/Datas/ImagesRues/_a trier_' -c 'Fourviere' -d 250 -f 5

```
