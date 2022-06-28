# GoProSort

Permet d'archiver un lot de photos et de preparer un upload vers KartaView, Mappilary ...

A partir d'un repertoire de photos en vrac :
- copie toutes les photos contenant en EXIF les photos de geoloc en les renommant "AAAA-MM-JJ_HHhMNmSS-FFFF.jpg" dans un repertoire "AAAA-MM-JJ - HHhMN" en se basant sur les datas EXIF
- copie dans un repertoires spécifique les fichiers qui repondent aux critères:
    * plus de X metres parcourus depuis la derniere
    * distance superieure à X metre du domicile
    * infos GPS presentes
    Ce repertoire pourra ensuité etre uploadé avec KartaView
    
Le programme genere un GPX de la trace complete et de la trace filtée ainsi qu'un rapport d'analyse
