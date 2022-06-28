# GoProSort

Permet d'archiver un lot de photos et de preparer un upload vers KartaView, Mappilary ...

A partir d'un repertoire de photos en vrac :
- copie toutes les photos en les renommant "AAAA-MM-JJ_HHhMNmSS-FFFF.jpg" dans un repertoire "AAAA-MM-JJ" en se basant sur les datas EXIF
- copie dans un repertoires spécifique les fichiers qui repondent aux critères:
    * plus de X metres parcourus depuis la derniere
    * distance superieure à X metre du domicile
    * infos GPS presentes
    
Le programme genere un GPX de la trace complete et de la trace filtée ainsi qu'un rapport d'analyse
