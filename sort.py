# /============================================================================
# | HISTORIQUE - Script de tri de photos gélocalisées
# |----------------------------------------------------------------------------
# | Changelog : [*] Bug fixes
# |             [+] New function
# |             [-] Update
# |-------+------------+-------------------------------------------------------
# | VERS  | DATE       | EVOLUTIONS
# |-------+------------+-------------------------------------------------------
# |       |            |
# | v0.2x | 05/07/2022 | - Nettoyage de code
# |       |            | - Arguments ajoutés pour generer ou pas les rep UP/BK
# |       |            | * Robustesse si EXIF cassé
# |       |            | * Interruption sur ESC
# |       |            |
# | v0.1x | 30/06/2022 | * Version initiale
# |       |            |
# \----------------------------------------------------------------------------
#
_version = 0.21

import glob
import os
from math import sin, cos, sqrt, atan2, asin, radians
from exif import Image
from datetime import datetime
import shutil
import argparse
import keyboard

pathVidage   = "/media/blueb/Datas/ImagesRues/0 - Vidage"
pathArchives = "/media/blueb/Datas/ImagesRues/1 - Archives"
pathUpload   = "/media/blueb/Datas/ImagesRues/2 - Upload"

pathVidage   = "c:/_eric_/0 - Vidage"
pathArchives = "c:/_eric_/1 - Archives"
pathUpload   = "c:/_eric_/2 - Upload"

prvLat = 0
prvLon = 0
curLat = 0
curLon = 0

#====== Point de départ (domicile) à filtrer et rayon de filtrage
#
dom_lat = 45.0000
dom_lon =  4.0000
dom_min = 500

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
trcName   = ""
trcPhotos = []
trcJour   = ""
trcName   = ""
#==============================================================================
# Fonction |  ComputeDist
#------------------------------------------------------------------------------
# Calcule la distance entre 2 point (lat/lon)
#
def ComputeDist(PLat, PLon, CLat, CLon):
    try:
        dDST=0
        # Rayon moyen de la terre
        #
        rEquateur = 6378.137	# Rayon équateur (km) : 6378.137
        rPole =     6356.752	# Rayon polaire (km)  : 6356.752

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
#
def ParseArgs():
    global pathVidage,trcName,photo_dmin,dom_min
    global noUpload, noArchive, noGpx

    parser = argparse.ArgumentParser(
        description =   "SORT.PY == Utilitaire de tri de photos : renomme les photos au "
                        "format 'HHhMNmSS-FFFF.jpg' et les range dans les répertoires " +
                        "définis ARCHIVE et UPLOAD.\n" +
                        "Dans le répertoire UPLOAD, les images trop proches du domicile "+
                        "ou trop proche d'une photo précédente sont filtrées.",
        epilog="Exemple: >python sort.py -r '/home/a/b/c/repertoire' -c 'comment' -d 250 -f 5")
    parser.add_argument( "-r", "--repertoire",
        type=str,
        action="store",
        default=pathVidage,
        help="Répertoire contenant les photos à trier (exemple: -r '/home/a/b/c/repertoire')")
    parser.add_argument( "-c", "--comment",
        type=str,
        action="store",
        default=trcName,
        help="Commentaire à ajouter au dossier  (exemple: -c 'Sortie vélo')")
    parser.add_argument( "-d", "--domicile",
        type=int,
        action="store",
        default=dom_min,
        help="Distance à filtrer autour du domicle en metres  (exemple: -d 200)")
    parser.add_argument( "-f", "--filtrage",
        type=int,
        action="store",
        default=photo_dmin,
        help="Distance minimale entre 2 photos en mètres  (exemple: -f 5)")
    parser.add_argument( "-nu", "--noupload",
        dest='noupload',
        action="store_true",
        help="Ne copie pas les fichiers dans le répertoire UPLOAD  (exemple: -nu)")
    parser.add_argument( "-na", "--noarchive",
        dest='noarchive',
        action="store_true",
        help="Ne copie pas les fichiers dans le répertoire ARCHIVE  (exemple: -na)")
    parser.add_argument( "-nx", "--nogpx",
        dest='nogpx',
        action="store_true",
        help="Ne génère pas le fichier GPX  (exemple: -nx)")
    args = parser.parse_args()

    pathVidage  = args.repertoire
    trcName     = args.comment
    photo_dmin  = args.filtrage
    dom_min     = args.domicile
    noUpload    = args.noupload
    noArchive   = args.noarchive
    noGpx       = args.nogpx

    print("Traitement du répertoire................%s"  % pathVidage)
    print("Commentaire à associer..................%s"  % trcName   )
    print("Distance minimale entre 2 photos........%sm" % photo_dmin)
    print("Zone de filtrage autour du domicile.....%sm" % dom_min   )
    print(f"Flag pour ne pas copier dans UPLOAD.....{ 'True' if noUpload  == True else 'False'}")
    print(f"Flag pour ne pas générer les GPX........{ 'True' if noGpx     == True else 'False'}")
    print(f"Flag pour ne pas copier dans ARCHIVE....{ 'True' if noArchive == True else 'False'}")

# =============================================================================
# Main
# -----------------------------------------------------------------------------
#
ParseArgs()
if not noGpx:
    gpxFullName         = pathVidage + "/trace-FULL.gpx"
    gpxFilteredName     = pathVidage + "/trace-FILTERED.gpx"
    gpxFullHandler      = open(gpxFullName , 'w')
    gpxFilteredHandler  = open(gpxFilteredName, 'w')
    FillGpx(gpxFullHandler,     gpxFullName,  'header',"",0,0,"",0)
    FillGpx(gpxFilteredHandler, gpxFilteredName, 'header',"",0,0,"",0)

fList = sorted(glob.glob(pathVidage+"/*.*"), key=os.path.basename)

for srcFile in fList:
    if keyboard.is_pressed('Esc'):
        print("*** Abort / ESC pressed ***")
        break
    if ((os.path.splitext(srcFile)[1]).upper())!=".JPG":
        print ("Fichier [%s] ignoré" % srcFile)
        continue
    ctrPhotos += 1
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
                if len(trcName) > 2:
                    trcJour = dtXF.strftime("%Y-%m-%d - %Hh%M") + " (" + trcName + ")"
                else:
                    trcJour = dtXF.strftime("%Y-%m-%d - %Hh%M")
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

                # Proteger le "gps_altitude", pas toujours présent
                #
                try:
                    gpxELE = exifInfo.gps_altitude
                except:
                    gpxELE = 0
            except:
                infosGPS = False

            if trcJour != prvJour:
                if not noArchive:
                    if os.path.isdir(pathArchives + "/" + trcJour):
                        print("Répertoire [%s/%s] existe déjà..." % (pathArchives, trcJour))
                    else:
                        os.mkdir(pathArchives + "/" + trcJour)
                if not noUpload:
                    if os.path.isdir(pathUpload + "/" + trcJour):
                        print("Répertoire [%s/%s] existe déjà..." % (pathUpload, trcJour))
                    else:
                        os.mkdir(pathUpload + "/" + trcJour)
                prvJour=trcJour

            # Proteger le "subsec_time", pas toujours présent, parfois 4 ou 6 digits
            #
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
                dstFile = pathArchives + "/" + trcJour + "/" + fileName
                print ("  Arch: [%s] -> [%s]" % (srcFile, dstFile))
                if infosGPS:
                    FillGpx(gpxFullHandler,  gpxFullName,     'point', gpxNAM, curLat, curLon, gpxDT,gpxELE)

                if (os.path.isfile(dstFile)):
                    print("Fichier [%s] exist" % dstFile)
                else:
                    shutil.copy(srcFile, dstFile)

            # Selon analyse, on copie ou pas dans le repertoire d'upload
            #
            if not noUpload:
                dstFile = pathUpload + "/" + trcJour + "/" + fileName
                print ("  Upld: [%s] -> [%s]" % (srcFile, dstFile))
                distPhoto = ComputeDist(prvLat, prvLon, curLat, curLon)
                distDom   = ComputeDist(dom_lat, dom_lon, curLat, curLon)
                if not infosGPS:
                    boolNGP=True
                    print("     *** sautée (pas d'infos GPS)")
                    ctrNoGps += 1
                elif (distPhoto < photo_dmin):
                    boolIMM=True
                    print("     *** sautée (pas assez d'écart avec la photo précédente)")
                    ctrImmobile += 1
                elif (distDom < dom_min):
                    boolDOM=True
                    print("     *** sautée (trop proche du domicile)")
                    ctrDomicile += 1
                else:
                    boolCOP=True
                    if (os.path.isfile(dstFile)):
                        print ("Fichier [%s] exist" % dstFile)
                    else:
                        shutil.copy(srcFile, dstFile)
                    #print ("     -> done")
                    ctrCopies += 1
                    prvLat=curLat
                    prvLon=curLon
                    FillGpx(gpxFilteredHandler, gpxFilteredName,'point', gpxNAM, curLat, curLon, gpxDT,gpxELE)

            if infosGPS:
                distTotal += distPhoto
                infoPhoto =(	ctrPhotos,	srcFile, fileName,	\
                                curLat,		curLon,  prvLat,	prvLon,  dLat, dLon, distPhoto,	\
                                int(distTotal),\
                                boolNGP,    ctrNoGps,	boolIMM,   ctrImmobile, boolDOM,    \
                                ctrDomicile,boolCOP,    ctrCopies, ctrNoExif )
                trcPhotos.append(infoPhoto)
            # Suppression ou pas du fichier traité
            # os.unlink(srcFile)
        except:
            print("EXIF except")
            ctrNoExif += 1

print("\nTotal:%d === Copiés:%d === NoGPS:%d === Filtré immobile:%d === Filtrées domicile:%d" % (ctrPhotos,ctrCopies,ctrNoGps,ctrImmobile,ctrDomicile))

if not noGpx:
    # Fermeture des GPX et copie des 2 fichiers dans le repertoire ARCHIVE
    #
    print("\nFermeture GPX", end="")
    FillGpx(gpxFullHandler,  gpxFullName,  'footer',"",0,0,"",0)
    gpxFullHandler.close()
    dstFile = pathArchives + "/" + trcJour + "/FULL-" + trcJour + ".gpx"
    shutil.copy(gpxFullName, dstFile)

    FillGpx(gpxFilteredHandler, gpxFilteredName, 'footer',"",0,0,"",0)
    gpxFilteredHandler.close()
    dstFile = pathArchives + "/" + trcJour + "/FILTERED-" + trcJour + ".gpx"
    shutil.copy(gpxFilteredName, dstFile)
    print("...ok")

with open(pathVidage + "/analyse.csv", 'w') as f:
    pt = ( "ctrPhotos;srcFile;fileName;curLat;  \
            curLon;prvLat;prvLon;dLat;          \
            dLon;distPhoto;distTotal;boolNGP;   \
            ctrNGP;boolIMM;ctrIMM;boolDOM;      \
            ctrDOM;boolCOP;ctrCOP;ctrNXF"  )
    print(pt, file=f)
    for i in range(0,len(trcPhotos)):
        print(str(trcPhotos[i]).replace(",",";").strip("[ (')]"), file=f)
f.close()

dstFile = pathArchives + "/" + trcJour + "/ANALYSE-" + trcJour + ".csv"
shutil.copy(pathVidage + "/analyse.csv", dstFile)

