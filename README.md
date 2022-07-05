# Photos-Sort

Photos-Sort permet de trier / archiver un lot de photos en vrac et de préparer un upload vers 
[KartaView](https://kartaview.org), [Mappilary](https://www.mapillary.com) ou autres ...
A partir d'un répertoire de photos en vrac :
* copie toutes les photos en les renommant au format `HHhMNmSS-FFFF.jpg` dans un répertoire 
d'archive `/AAAA-MM-JJ - HHhMN/` (l'heure contenue dans le nom du répertoire est l'heure de la première photo du lot)
* copie les photos en les renommant au format `HHhMNmSS-FFFF.jpg` dans le répertoire d'upload limité aux photos qui :
  - contiennent un EXIF correct
  - ont recu une géoloc GPS correcte
  - sont à plus de X mètres de la dernière photo
  - sont à plus de Y mètres du domicile
  
Ce répertoire pourra ensuite etre uploadé avec [KartaView upload](https://github.com/kartaview/upload-scripts)

Le programme génère aussi
* un GPX de la trace complète (nommé `FULL-AAAA-MM-JJ - HHhMN (commentaire).gpx`)
* un GPX de la trace filtrée donc sans les images en double ou trop proches du domicile (nommé `FILTERED-AAAA-MM-JJ - HHhMN (commentaire).gpx`)
* un rapport d'analyse (`Analyse-AAAA-MM-JJ - HHhMN (commentaire).csv`)

```
usage: sort.py [-h] [-r REPERTOIRE] [-c COMMENT] [-d DOMICILE] [-f FILTRAGE] [-nu NOUPLOAD] [-na NOARCHIVE] [-nx NOGPX]

SORT.PY == Utilitaire de tri de photos : renome les photos au format 'HHhMNmSS-FFFF.jpg' et les range dans les 
répertoires ARCHIVE et UPLOAD. Dans le répertoire UPLOAD, les images trop proches du domicile ou trop proche 
de la dernière photo envoyée sont filtrées.

options:
  -h, --help            show this help message and exit
  -r, --repertoire "/x/y/z"
                        Répertoire contenant les photos à trier (exemple: -r '/media/blueb/Datas/ImagesRues/_a trier_')
  -c, --comment "comment"
                        Commentaire à ajouter au dossier (exemple: -c 'Fourviere')
  -d, --domicile <metres>
                        Distance à filtrer autour du domicle en metres (exemple: -d 200)
  -f, --filtrage <metres>
                        Distance minimale entre 2 photos en metres (exemple: -f 5)
  -nu, --noupload
                        Ne copie pas les fichiers dans le repertoire UPLOAD (exemple: -nu)
  -na, --noarchive
                        Ne copie pas les fichiers dans le repertoire ARCHIVE (exemple: -na)
  -nx, --nogpx
                        Ne genere pas le fichier GPX (exemple: -nx)

Exemple: >Python3 sort.py -r '/media/blueb/Datas/ImagesRues/_a trier_' -c 'Fourviere' -d 250 -f 5 -nu

```
