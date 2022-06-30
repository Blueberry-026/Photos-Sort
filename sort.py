import glob
import os
from math import sin, cos, sqrt, atan2, asin, radians
from exif import Image
from datetime import datetime
import shutil
import argparse
import sys

srcBaseDir = "c:/_eric_/_atrier"
gopBaseDir = "c:/_eric_/_arch"
krtBaseDir = "c:/_eric_/_kv"

srcBaseDir = "/media/blueb/Datas/ImagesRues/_a trier_"
gopBaseDir = "/media/blueb/Datas/ImagesRues/Archives"
krtBaseDir = "/media/blueb/Datas/ImagesRues/Kartaview"

prvLat = 0
prvLon = 0
curLat = 0
curLon = 0

#====== Point de départ à filtrer
#
dom_lat = 45.7442
dom_lon =  4.8343
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

prvJour   = ""
firstPos  = True
distTotal = 0
distPhoto = 0
distDom   = 0

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
    global srcBaseDir,nameDir,photo_dmin,dom_min

    parser = argparse.ArgumentParser(description="Tri de photos",
                                     epilog="Exemple: >Python3 sort.py -r '/media/blueb/Datas/ImagesRues/_a trier_' -c 'boulot' -d 250 -f 5")
    parser.add_argument(
        "-r", "--repertoire",
        type=str,
        action="store",
        default=srcBaseDir,
        help="Répertoire contenant les photos à trier\n(exemple : -r '/media/blueb/Datas/ImagesRues/_a trier_'")
    parser.add_argument(
        "-c", "--comment",
        type=str,
        action="store",
        default=nameDir,
        help="Commentaire à ajouter au dossier\n(exemple : -c 'Fourviere')")
    parser.add_argument(
        "-d", "--domicile",
        type=str,
        action="store",
        default=dom_min,
        help="Distance à filtrer autour du domicle en metres\n(exemple : -d 200")
    parser.add_argument(
        "-f", "--filtrage",
        type=str,
        action="store",
        default=photo_dmin,
        help="Distance minimale entre 2 photos en metres\n(exemple : -f 5")
    args = parser.parse_args()

    srcBaseDir = args.repertoire
    nameDir = args.comment
    photo_dmin = args.filtrage
    dom_min = args.domicile

# =============================================================================
# Main
# -----------------------------------------------------------------------------
#
gpxFullName     = "traceFULL.gpx"
gpxKviewName    = "traceKV.gpx"
gpxFullHandler  = open(gpxFullName , 'w')
gpxKviewHandler = open(gpxKviewName, 'w')
FillGpx(gpxFullHandler,  gpxFullName,  'header',"",0,0,"",0)
FillGpx(gpxKviewHandler, gpxKviewName, 'header',"",0,0,"",0)
lstPhotos=[]
repJour=""
nameDir=""

fList    = sorted(glob.glob(srcBaseDir+"/*.JPG"), key=os.path.basename)

ParseArgs()

for srcFile in fList:
    ctrPhotos=ctrPhotos+1
#    if ctrPhotos>100:
#        break
    print("====== Fichier %d/%d) == %s == " % (ctrPhotos,len(fList),srcFile))
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

                    # Decoder l'heure GPS de la premiere photo, calculer l'offeset avec l'heure EXIF et la rajouter
                    # ensuite à toutes les photos.
                    #
                    strGPS = "%s %2.2d:%2.2d:%2.2d" % ( exifInfo.gps_datestamp,
                                                        int(exifInfo.gps_timestamp[0]),
                                                        int(exifInfo.gps_timestamp[1]),
                                                        int(exifInfo.gps_timestamp[2]))
                    #dtGPS    = datetime.strptime(strGPS, "%Y:%m:%d %H:%M:%S")
                    #offsetTM = dtGPS-dtXF
                    #repJour  = dtGPS.strftime("%Y-%m-%d - %Hh%M")
                    firstPos = False
                dLat   = abs(curLat - prvLat)
                dLon   = abs(curLon - prvLon)
                gpxDT  = dtXF.strftime("%Y-%m-%dT%H:%M:%S")
                gpxELE = exifInfo.gps_altitude
            except:
                infosGPS = False

            if repJour != prvJour:
                try:
                    os.mkdir(gopBaseDir + "/" + repJour)
                except:
                    print ("Répertoire [%s/%s] existe déjà..." % (gopBaseDir,repJour))
                try:
                    os.mkdir(krtBaseDir + "/" + repJour)
                except:
                    print ("Répertoire [%s/%s] existe déjà..." % (krtBaseDir,repJour))
            prvJour=repJour
        except:
            print("EXIF except")

    #if not firstPos:
    #	dtXF = dtXF + offsetTM
    #fileName = dtXF.strftime("%Y-%m-%d_%Hh%Mm%S")
    #fileName = fileName + "-" + format("%4.4d" % int(exifInfo.subsec_time )) + ".jpg"

    fileName = "%s - %4.4d.jpg" % (dtXF.strftime("%Y-%m-%d_%Hh%Mm%S") , int(exifInfo.subsec_time ))
    gpxNAM=fileName
    fileName = "%s-%4.4d.jpg" % (dtXF.strftime("%Hh%Mm%S") , int(exifInfo.subsec_time ))
    # Dans tous les cas, on archive dans le backup local
    #
    dstFile = gopBaseDir + "/" + repJour + "/" + fileName
    print ("  Arch: [%s] -> [%s]" % (srcFile, dstFile))
    if infosGPS:
      FillGpx(gpxFullHandler,  gpxFullName,     'point', gpxNAM, curLat, curLon, gpxDT,gpxELE)

    if (os.path.isfile(dstFile)):
        print("Fichier [%s] exist" % dstFile)
    else:
        shutil.copy(srcFile, dstFile)

    #print("      -> done")

    # Selon analyse, on copie ou pas dans le rep d'upload KV
    #
    dstFile = krtBaseDir + "/" + repJour + "/" + fileName
    print ("  Krtv: [%s] -> [%s]" % (srcFile, dstFile))
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
        trpPhoto =(	ctrPhotos,	\
                    srcFile,	\
                    fileName,	\
                    curLat,		\
                    curLon,		\
                    prvLat,		\
                    prvLon,		\
                    dLat,		\
                    dLon,		\
                    distPhoto,	\
                    int(distTotal),\
                    boolNGP,    \
                    ctrNoGps,	\
                    boolIMM,    \
                    ctrImmobile,\
                    boolDOM,    \
                    ctrDomicile,\
                    boolCOP,     \
                    ctrCopies	\
                    )
        lstPhotos.append(trpPhoto)

print("\nTotal:%d === Copiés:%d === NoGPS:%d === Filtré immobile:%d === Filtrées domicile:%d" % (ctrPhotos,ctrCopies,ctrNoGps,ctrImmobile,ctrDomicile))

print("\nFermeture GPX")
FillGpx(gpxFullHandler,  gpxFullName,  'footer',"",0,0,"",0)
FillGpx(gpxKviewHandler, gpxKviewName, 'footer',"",0,0,"",0)
gpxKviewHandler.close()
gpxFullHandler.close()
print("\nFermeture GPX...ok")

dstFile = gopBaseDir + "/" + repJour + "/Trace-" + repJour + " (full).gpx"
shutil.copy(gpxFullName, dstFile)

dstFile = krtBaseDir + "/" + repJour + "/Trace-" + repJour + " (kv).gpx"
shutil.copy(gpxKviewName, dstFile)

dstFile = gopBaseDir + "/" + repJour + "/Analyse-" + repJour + ".csv"
shutil.copy("analyse.csv", dstFile)

with open('analyse.csv', 'w') as f:
    pt = (  "ctrPhotos; \
            srcFile; \
            fileName; \
            curLat; \
            curLon; \
            prvLat; \
            prvLon; \
            dLat; \
            dLon; \
            distPhoto; \
            distTotal; \
            boolNGP; \
            ctrNGP; \
            boolIMM; \
            ctrIMM; \
            boolDOM; \
            ctrDOM; \
            boolCOP; \
            ctrCOP")
    #print(pt)
    print(pt, file=f)
    for i in range(0,len(lstPhotos)):
        pt = (  "%d;%s;%s;\
                %7.5f;%7.5f;%7.5f;%7.5f;%7.5f;%7.5f;\
                %6.5f; %d; \
                %d;%d;%d;%d;%d;%d;%d;%d" % ( \
                    lstPhotos[i][0],	# ctrPhotos \
                    lstPhotos[i][1],	# srcFile   \
                    lstPhotos[i][2],	# fileName  \
                    lstPhotos[i][3],	# curLat    \
                    lstPhotos[i][4],	# curLon    \
                    lstPhotos[i][5],	# prvLat    \
                    lstPhotos[i][6],	# prvLon    \
                    lstPhotos[i][7],	# dLat      \
                    lstPhotos[i][8],	# dLon      \
                    lstPhotos[i][9],	# dist      \
                    lstPhotos[i][10],	# dstTotal  \
                    lstPhotos[i][11],	# boolNGP   \
                    lstPhotos[i][12],	# ctrNGP    \
                    lstPhotos[i][13],	# boolIMM   \
                    lstPhotos[i][14],	# ctrIMM    \
                    lstPhotos[i][15],	# boolDOM   \
                    lstPhotos[i][16],	# ctrDOM    \
                    lstPhotos[i][17],	# boolCOP   \
                    lstPhotos[i][18],	# ctrCOP    \
                    ))
        #print(pt)
        print(pt, file=f)
f.close()