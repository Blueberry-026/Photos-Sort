import glob
import os
from math import sin, cos, sqrt, atan2, asin, radians
from exif import Image
from datetime import datetime
import shutil

srcBaseDir = "/media/blueb/Datas/ImagesRues/GoPro/_a trier_"
dstBaseDir = "/media/blueb/Datas/ImagesRues/GoPro/"
krtBaseDir = "/media/blueb/Datas/ImagesRues/Kartaview"

srcBaseDir = "c:/_eric_/_img"
dstBaseDir = "c:/_eric_/_gop"
krtBaseDir = "c:/_eric_/_kv"

#====== Point de départ à filtrer
#
dom_lat = 45.0000
dom_lon =  4.0000
dom_min = 200

#====== Distance mini entre 2 photos
#
photo_dmin = 5

#====== Stats
#
ctrPhotos	= 0		# Total de photos dans le répertoire d'entrée
ctrCopies	= 0 	# Total de photos bonnes donc copiées pour upload Kartview
ctrImmobile	= 0		# Total de photos non copiées car immobiles
ctrDomicile	= 0 	# Total de photos non copiées car proche domicile
ctrNoGps	= 0 	# Total de photos non copiées car non géotaggès

prvJour  = ""
firstPos = True
fList    = sorted(glob.glob(srcBaseDir+"/*.JPG"), key=os.path.basename)
dstTotal   = 0
dstPhoto     = 0

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
def FillGpx(handler, fGpx, code, gpxLat, gpxLon, gpxDat, gpxEle):
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
            handler.write("            <name>abc</name>\n")
            handler.write("         </trkpt>\n")
        #else:
        #    print("Position 0/0 non écrite")
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
    dd = float(pos[0]) + float(pos[1])/60 + float(pos[2])/(60*60);
    return dd;

# =============================================================================
# Main
# -----------------------------------------------------------------------------
#
gpxFullName     = "traceFULL.gpx"
gpxKviewName    = "traceKV.gpx"
gpxFullHandler  = open(gpxFullName , 'w')
gpxKviewHandler = open(gpxKviewName, 'w')
FillGpx(gpxFullHandler,  gpxFullName,  'header',0,0,"",0)
FillGpx(gpxKviewHandler, gpxKviewName, 'header',0,0,"",0)
lstPhotos=[]

for srcFile in fList:
    ctrPhotos=ctrPhotos+1
    if ctrPhotos>200:
    	break
    print("====== Fichier %d/%d) == %s == " % (ctrPhotos,len(fList),srcFile))
    boolDOM=False
    boolNGP=False
    boolIMM=False
    boolCOP=False
  
    with open(srcFile, 'rb') as image_file:
        exifInfo = Image(image_file)
        dtXF = datetime.strptime(exifInfo.datetime, '%Y:%m:%d %H:%M:%S')
        if ctrPhotos == 1:
            repJour = dtXF.strftime("%Y-%m-%d")
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
                dtGPS    = datetime.strptime(strGPS, "%Y:%m:%d %H:%M:%S")
                offsetTM = dtGPS-dtXF
                repJour  = dtGPS.strftime("%Y-%m-%d")
                firstPos = False
            dLat   = abs(curLat - prvLat)
            dLon   = abs(curLon - prvLon)
            gpxDT  = dtXF.strftime("%Y-%m-%dT%H:%M:%S")
            gpxELE = exifInfo.gps_altitude
        except:
            infosGPS = False

        if repJour != prvJour:
            try:
                os.mkdir(dstBaseDir + "/" + repJour)
            except:
                print ("Répertoire [%s/%s] existe déjà..." % (dstBaseDir,repJour))
            try:
                os.mkdir(krtBaseDir + "/" + repJour)
            except:
                print ("Répertoire [%s/%s] existe déjà..." % (krtBaseDir,repJour))
        prvJour=repJour

    #if not firstPos:
    #	dtXF = dtXF + offsetTM
    fileName = dtXF.strftime("%Y-%m-%d_%Hh%Mm%S")
    fileName = fileName + "-" + format("%4.4d" % int(exifInfo.subsec_time )) + ".jpg"
    # Dans tous les cas, on archive dans le backup local
    #
    dstFile = dstBaseDir + "/" + repJour + "/" + fileName
    print ("  Archive locale [%s] -> [%s]" % (srcFile, dstFile))
    if infosGPS:
      FillGpx(gpxFullHandler,  gpxFullName,     'point', curLat, curLon, gpxDT,gpxELE)
    shutil.copy(srcFile, dstFile)
    print("      -> done")

    # Selon analyse, on copie ou pas dans le rep d'upload KV
    #
    dstFile = krtBaseDir + "/" + repJour + "/" + fileName
    print ("  Upload Kartaview [%s] -> [%s]" % (srcFile, dstFile))
    distPT  = ComputeDist(prvLat, prvLon, curLat, curLon)
    distDOM = ComputeDist(dom_lat, dom_lon, curLat, curLon)
    if not infosGPS:
        boolNGP=True
        print("     *** sautée (pas d'infos GPS)")
        ctrNoGps = ctrNoGps + 1
    elif (distPT < photo_dmin):
        boolIMM=True
        print("     *** sautée (pas assez d'écart avec la photo précédente) %f/%f" % (dLat, dLon))
        ctrImmobile = ctrImmobile + 1
    elif (distDOM < dom_min):
        boolDOM=True
        print("     *** sautée (trop proche du domicile) %f/%f" % ((curLat - dom_lat),(curLon - dom_lon) ) )
        ctrDomicile = ctrDomicile + 1
    else:
        boolCOP=True
        shutil.copy(srcFile, dstFile)
        print ("     -> done  | mouvement = %f/%f | domicile = %f/%f" % (dLat,dLon,abs(curLat - dom_lat),abs(curLon - dom_lon)) )
        ctrCopies=ctrCopies+1
        prvLat=curLat
        prvLon=curLon
        FillGpx(gpxKviewHandler, gpxKviewName,'point', curLat, curLon, gpxDT,gpxELE)

    #os.unlink(srcFile)
    if infosGPS:
        dstTotal += dstPhoto
        trpPhoto =(	ctrPhotos,	\
                    srcFile,	\
                    fileName,	\
                    curLat,		\
                    curLon,		\
                    prvLat,		\
                    prvLon,		\
                    dLat,		\
                    dLon,		\
                    dstPhoto,	\
                    int(dstTotal),\
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

print("\n\n\nTotal:%d === Copiés:%d === NoGPS:%d === Filtré immobile:%d === Filtrées domicile:%d" % (ctrPhotos,ctrCopies,ctrNoGps,ctrImmobile,ctrDomicile))
         
FillGpx(gpxFullHandler,  gpxFullName,  'footer',0,0,"",0)
FillGpx(gpxKviewHandler, gpxKviewName, 'footer',0,0,"",0)

dstFile = dstBaseDir + "/" + repJour + "/Trace-" + repJour + " (full).gpx"
#shutil.move(gpxFullName, dstFile)

dstFile = krtBaseDir + "/" + repJour + "/Trace-" + repJour + " (kv).gpx"
#shutil.move(gpxKviewName, dstFile)

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
            dist; \
            dstTotal; \
            boolNGP; \
            ctrNGP; \
            boolIMM; \
            ctrIMM; \
            boolDOM; \
            ctrDOM; \
            boolCOP; \
            ctrCOP")
    print(pt)
    print(pt, file=f)
    for i in range(0,len(lstPhotos)):
        pt = (  "%d;%s;%s;\
                %7.5f;%7.5f;%7.5f;%7.5f;%7.5f;%7.5f;\
                %6.5f; %d; \
                %d;%d;%d;%d;%d;%d;%d;%d"	% \
          (         lstPhotos[i][0],	\
                    lstPhotos[i][1],	\
                    lstPhotos[i][2],	\
                    lstPhotos[i][3],	\
                    lstPhotos[i][4],	\
                    lstPhotos[i][5],	\
                    lstPhotos[i][6],	\
                    lstPhotos[i][7],	\
                    lstPhotos[i][8],	\
                    lstPhotos[i][9],	\
                    lstPhotos[i][10],	\
                    lstPhotos[i][11],	\
                    lstPhotos[i][12],	\
                    lstPhotos[i][13],	\
                    lstPhotos[i][14],	\
                    lstPhotos[i][15],	\
                    lstPhotos[i][16],	\
                    lstPhotos[i][17],	\
                    lstPhotos[i][18],	\
                    ))
        print(pt)
        print(pt, file=f)