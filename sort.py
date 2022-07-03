# /============================================================================
# | HISTORIQUE - Script de décodage de trames NMEA
# |----------------------------------------------------------------------------
# | Changelog : [*] Bug fixes
# |             [+] New function
# |             [-] Update
# |-------+------------+-------------------------------------------------------
# | VERS  | DATE       | EVOLUTIONS
# |-------+------------+-------------------------------------------------------
# |       |            |
# | v0.1x | 01/07/2022 | * Version initiale
# |       |            |
# |       |            |
# \----------------------------------------------------------------------------
#
_version = 0.11

import glob
import os
from math import sin, cos, sqrt, atan2, asin, radians
from exif import Image
from datetime import datetime
import shutil
import argparse
import sys

pathVidage   = "c:/_eric_/0 - Vidage"
pathArchives = "c:/_eric_/1 - Archives"
pathUpload   = "c:/_eric_/2 - Upload"

pathVidage   = "/media/blueb/Datas/ImagesRues/0 - Vidage"
pathArchives = "/media/blueb/Datas/ImagesRues/1 - Archives"
pathUpload   = "/media/blueb/Datas/ImagesRues/2 - Upload"

prvLat = 0
prvLon = 0
curLat = 0
curLon = 0

#====== Point de départ à filtrer
#
dom_lat = 45.0000
dom_lon =  4.0000
dom_min = 200

#====== Distance mini entre 2 photos
#
photo_dmin = 4

#====== Stats
#
ctrPhotos	= 0		# Total de photos dans le répertoire d'entrée
ctrCopies	= 0 	# Total de photos bonnes donc copiées pour upload Kartview
ctrImmobile	= 0		# Total de photos non copiées car immobiles
ctrDomicile	= 0 	# Total de photos non copiées car proche domicile
ctrNoGps	= 0 	# Total de photos non copiées car non géotaggès
ctrNoExif	= 0 	# Total de photos non copiées car non géotaggès

prvJour   = ""
firstPos  = True
distTotal = 0
distPhoto = 0
distDom   = 0

noUpload  = False
noArchive = False
noGpx     = False

#==============================================================================
# Fonction |  ComputeDist
#------------------------------------------------------------------------------
#
def ComputeDist(PLat, PLon, CLat, CLon):
    try:
        dDST=0
        # Rayon moyen de la terre
        #
        rEquateur = 6378.137	# Rayon équateur (km) : 6378.137
        rPole = 6356.752		# Rayon polaire (km)  : 6356.752

        # Estimation du rayon à la latitude recue
        #
        radius = rPole + (CLat * (rEquateur - rPole) / 90)

        # Distance LAT/LON parcourue depuis le dernier appel
        #
        CLon, CLat = map(radians, [CLon, CLat])
        PLon, PLat = map(radians, [PLon, PLat])

        deltaLat = (CLat - PLat)
        deltaLon = (CLon - PLon)

        a = sin(deltaLat / 2) ** 2 + cos(CLat) * cos(PLat) * sin(deltaLon / 2) ** 2
        c = 2 * asin(sqrt(a))
        dDST = (radius * c) *1000
        if dDST<1:
            print("Distance 0 !!")
    except Exception as e:
        print("   !!! ComputeDist EXCEPT [%s] " % e)
    return dDST

# =============================================================================
# Fonction |  FillGpx
# -----------------------------------------------------------------------------
# Selon le code recu, écrit soit l'entête du fichier GPX, soit
# le point courant soit les lignes de fin de fichier
#
def FillGpx(handler, fGpx, code, gpxNAM, gpxLat, gpxLon, gpxDat, gpxEle):
    if (not noGpx):
        if code == 'header':
            handler.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n")
            handler.write("<gpx version=\"1.0\">\n")
            handler.write("   <trk>\n")
            handler.write("      <name>" + fGpx + "</name>\n")
            handler.write("      <trkseg>\n")
        elif code == 'point':
            if ((gpxLat != 0) and (gpxLon != 0)):
                handler.write("         <trkpt lat='%f' lon='%f'>\n" % (gpxLat, gpxLon))
                handler.write("            <ele>%d</ele>\n" % gpxEle)
                handler.write("            <time>%s</time>\n" % gpxDat)
                handler.write("            <name>%s</name>\n" % gpxNAM)
                handler.write("         </trkpt>\n")
        elif code == 'footer':
            handler.write("      </trkseg>\n")
            handler.write("   </trk>\n")
            handler.write("</gpx>\n")
        else:
            print("\n   -> FillGpx : code [%s] erroné" % code)

# =============================================================================
# Fonction |  ConvertDMS_DDD
# -----------------------------------------------------------------------------
#
def ConvertDMS_DDD(pos):
    dd = float(pos[0]) + float(pos[1])/60 + float(pos[2])/(60*60)
    return dd

# =============================================================================
# Fonction |  ParseArgs
# -----------------------------------------------------------------------------
# Exemple:
#    --repertoire "/media/blueb/Datas/ImagesRues/GoPro/_27-Boulot" --comment "toto" --domicile 200 --filtrage 5
def ParseArgs():
    global pathVidage,nameDir,photo_dmin,dom_min
    global noUpload, noArchive, noGpx

    parser = argparse.ArgumentParser(description=   "SORT.PY == Utilitaire de tri de photos : renome les photos au format 'HHhMNmSS-FFFF.jpg' et " +
                                                    "les range dans les répertoires ARCHIVE et UPLOAD.\n" +
                                                    "Dans le répertoire UPLOAD, les images trop proches du domicile ou trop proche d'une photo précédente " +
                                                    "sont filtrées.",
                                     epilog="Exemple: >Python3 sort.py -r '/media/blueb/Datas/ImagesRues/_a trier_' -c 'Fourviere' -d 250 -f 5")
    parser.add_argument(
        "-r", "--repertoire",
        type=str,
        action="store",
        default=pathVidage,
        help="Répertoire contenant les photos à trier\n(exemple: -r '/media/blueb/Datas/ImagesRues/_a trier_')")
    parser.add_argument(
        "-c", "--comment",
        type=str,
        action="store",
        default=nameDir,
        help="Commentaire à ajouter au dossier\n(exemple: -c 'Fourviere')")
    parser.add_argument(
        "-d", "--domicile",
        type=int,
        action="store",
        default=dom_min,
        help="Distance à filtrer autour du domicle en metres\n(exemple: -d 200)")
    parser.add_argument(
        "-f", "--filtrage",
        type=int,
        action="store",
        default=photo_dmin,
        help="Distance minimale entre 2 photos en metres\n(exemple: -f 5)")
    parser.add_argument(
        "-nu", "--noupload",
        type=bool,
        action="store",
        default=False,
        help="Ne copie pas les fichiers dans le repertoire UPLOAD\n(exemple: -nu 1)")
    parser.add_argument(
        "-na", "--noarchive",
        type=bool,
        action="store",
        default=False,
        help="Ne copie pas les fichiers dans le repertoire ARCHIVE\n(exemple: -na 1)")
    parser.add_argument(
        "-nx", "--nogpx",
        type=bool,
        action="store",
        default=False,
        help="Ne genere pas le fichier GPX\n(exemple: -nx 1)")
    args = parser.parse_args()

    pathVidage  = args.repertoire
    nameDir     = args.comment
    photo_dmin  = args.filtrage
    dom_min     = args.domicile
    noUpload    = args.noupload
    noArchive   = args.noarchive
    noGpx       = args.nogpx

    print("Traitement du répertoire................%s" % pathVidage)
    print("Commentaire à associer..................%s" % nameDir   )
    print("Distance minimale entre 2 photos........%sm" % photo_dmin)
    print("Zone de filtrage autour du domicile.....%sm" % dom_min   )
    print("Flag pour ne pas copier dans UPLOAD.....%d" % noUpload  )
    print("Flag pour ne pas copier dans ARCHIVE....%d" % noArchive )
    print("Flag pour ne pas générer les GPX........%d" % noGpx     )

# =============================================================================
# Main
# -----------------------------------------------------------------------------
#
if (not noGpx) :
    gpxFullName     = pathVidage + "/traceFULL.gpx"
    gpxKviewName    = pathVidage + "/traceKV.gpx"
    gpxFullHandler  = open(gpxFullName , 'w')
    gpxKviewHandler = open(gpxKviewName, 'w')
    FillGpx(gpxFullHandler,  gpxFullName,  'header',"",0,0,"",0)
    FillGpx(gpxKviewHandler, gpxKviewName, 'header',"",0,0,"",0)
lstPhotos   = []
repJour     = ""
nameDir     = ""

ParseArgs()

fList    = sorted(glob.glob(pathVidage+"/*.*"), key=os.path.basename)

for srcFile in fList:
    if ((os.path.splitext(srcFile)[1]).upper())!=".JPG":
        print ("Fichier [%s] ignoré" % srcFile)
        continue
    ctrPhotos=ctrPhotos+1
#    if ctrPhotos>100:
#        break
    print("====== Fichier %d/%d) == %s == Version %4.2f ==" % (ctrPhotos,len(fList),srcFile,_version))
    boolDOM=False
    boolNGP=False
    boolIMM=False
    boolCOP=False
  
    with open(srcFile, 'rb') as image_file:
        try:
            exifInfo = Image(image_file)
            dtXF = datetime.strptime(exifInfo.datetime, '%Y:%m:%d %H:%M:%S')
            if ctrPhotos == 1:
                if len(nameDir) > 2:
                    repJour = dtXF.strftime("%Y-%m-%d - %Hh%M") + " (" + nameDir + ")"
                else:
                    repJour = dtXF.strftime("%Y-%m-%d - %Hh%M")
            try:
                curLat = ConvertDMS_DDD(exifInfo.gps_latitude)
                curLon = ConvertDMS_DDD(exifInfo.gps_longitude)

                # Si pas d'info GPS (garage au début ou tunnel ...) il n'y a pas encore de GPS donc on part en exemption
                # Sinon, recuperer lat/lon/heure ...
                #
                infosGPS = True
                if firstPos:
                    prvLat = ConvertDMS_DDD(exifInfo.gps_latitude)
                    prvLon = ConvertDMS_DDD(exifInfo.gps_longitude)
                    firstPos = False
                dLat   = abs(curLat - prvLat)
                dLon   = abs(curLon - prvLon)
                gpxDT  = dtXF.strftime("%Y-%m-%dT%H:%M:%S")
                try:
                    gpxELE = exifInfo.gps_altitude
                except:
                    gpxELE = 0
            except:
                infosGPS = False

            if repJour != prvJour:
                if os.path.isdir(pathArchives + "/" + repJour):
                    print("Répertoire [%s/%s] existe déjà..." % (pathArchives, repJour))
                else:
                    os.mkdir(pathArchives + "/" + repJour)
                if os.path.isdir(pathUpload + "/" + repJour):
                    print("Répertoire [%s/%s] existe déjà..." % (pathUpload, repJour))
                else:
                    os.mkdir(pathUpload + "/" + repJour)

                prvJour=repJour

            try:
                fileName = "%s - %4.4d.jpg" % (dtXF.strftime("%Y-%m-%d_%Hh%Mm%S") , int(exifInfo.subsec_time ))
                gpxNAM = fileName
                fileName = "%s-%4.4d.jpg" % (dtXF.strftime("%Hh%Mm%S"), int(exifInfo.subsec_time))
            except:
                fileName = "%s - 0000.jpg" % (dtXF.strftime("%Y-%m-%d_%Hh%Mm%S"))
                gpxNAM=fileName
                fileName = "%s-0000.jpg" % (dtXF.strftime("%Hh%Mm%S"))

            # Dans tous les cas, on archive dans le backup local si on n'a pas
            # de flag contraire
            #
            if not noArchive:
                dstFile = pathArchives + "/" + repJour + "/" + fileName
                print ("  Arch: [%s] -> [%s]" % (srcFile, dstFile))
                if infosGPS:
                    FillGpx(gpxFullHandler,  gpxFullName,     'point', gpxNAM, curLat, curLon, gpxDT,gpxELE)

                if (os.path.isfile(dstFile)):
                    print("Fichier [%s] exist" % dstFile)
                else:
                    shutil.copy(srcFile, dstFile)

            # Selon analyse, on copie ou pas dans le rep d'upload KV
            #
            if (noUpload==False):
                dstFile = pathUpload + "/" + repJour + "/" + fileName
                print ("  Upld: [%s] -> [%s]" % (srcFile, dstFile))
                distPhoto = ComputeDist(prvLat, prvLon, curLat, curLon)
                distDom   = ComputeDist(dom_lat, dom_lon, curLat, curLon)
                if not infosGPS:
                    boolNGP=True
                    print("     *** sautée (pas d'infos GPS)")
                    ctrNoGps = ctrNoGps + 1
                elif (distPhoto < photo_dmin):
                    boolIMM=True
                    print("     *** sautée (pas assez d'écart avec la photo précédente)")
                    ctrImmobile = ctrImmobile + 1
                elif (distDom < dom_min):
                    boolDOM=True
                    print("     *** sautée (trop proche du domicile)")
                    ctrDomicile = ctrDomicile + 1
                else:
                    boolCOP=True
                    if (os.path.isfile(dstFile)):
                        print ("Fichier [%s] exist" % dstFile)
                    else:
                        shutil.copy(srcFile, dstFile)
                    #print ("     -> done")
                    ctrCopies=ctrCopies+1
                    prvLat=curLat
                    prvLon=curLon
                    FillGpx(gpxKviewHandler, gpxKviewName,'point', gpxNAM, curLat, curLon, gpxDT,gpxELE)

            #os.unlink(srcFile)
            if infosGPS:
                distTotal += distPhoto
                trpPhoto =(	ctrPhotos,	srcFile, fileName,	\
                            curLat,		curLon,  prvLat,	prvLon,  dLat, dLon, distPhoto,	\
                            int(distTotal),\
                            boolNGP,    ctrNoGps,	boolIMM,   ctrImmobile, boolDOM,    \
                            ctrDomicile,boolCOP,    ctrCopies, ctrNoExif )
                lstPhotos.append(trpPhoto)
        except:
            print("EXIF except")
            ctrNoExif+=1

print("\nTotal:%d === Copiés:%d === NoGPS:%d === Filtré immobile:%d === Filtrées domicile:%d" % (ctrPhotos,ctrCopies,ctrNoGps,ctrImmobile,ctrDomicile))

if (not noGpx) :
    print("\nFermeture GPX", end="")
    FillGpx(gpxFullHandler,  gpxFullName,  'footer',"",0,0,"",0)
    FillGpx(gpxKviewHandler, gpxKviewName, 'footer',"",0,0,"",0)
    gpxKviewHandler.close()
    gpxFullHandler.close()
    print("...ok")

with open(pathVidage + "/analyse.csv", 'w') as f:
    pt = ( "ctrPhotos;srcFile;fileName;curLat;  \
            curLon;prvLat;prvLon;dLat;          \
            dLon;distPhoto;distTotal;boolNGP;   \
            ctrNGP;boolIMM;ctrIMM;boolDOM;      \
            ctrDOM;boolCOP;ctrCOP;ctrNXF"  )
    print(pt, file=f)
    for i in range(0,len(lstPhotos)):
        print(str(lstPhotos[i]).replace(",",";").strip("[ (')]"), file=f)
f.close()

if (not noGpx) :
    dstFile = pathArchives + "/" + repJour + "/FULL-" + repJour + ".gpx"
    shutil.copy(gpxFullName, dstFile)
    dstFile = pathArchives + "/" + repJour + "/FILTERED-" + repJour + ".gpx"
    shutil.copy(gpxKviewName, dstFile)

dstFile = pathArchives + "/" + repJour + "/ANALYSE-" + repJour + ".csv"
shutil.copy(pathVidage + "/analyse.csv", dstFile)

