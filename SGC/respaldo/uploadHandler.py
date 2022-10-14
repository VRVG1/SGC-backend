def handleUploadFile(file):
    with open('./var/restauracion/BackupSGC.zip', 'wb') as dst:
        for chunk in file.chunks():
            dst.write(chunk)
        pass
