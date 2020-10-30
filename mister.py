import os
import util
import shutil
import ntpath
import platform
import PIL
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw


# Removed unused CDs
def removeUnusedCds(game, localGameOutputDir, logger):
    unusedCds = {
        'heromm2d': '.\\CD\\Heroes of Might and Magic 2.cue',
        'VirtSqua': '.\\cd\\V_SQUAD.CUE',
        'SSN21Se': '.\\cd\\SEAWOLF___.cue',
        'FIFAInte': '.\\CD\\FIFA.International.Soccer.cue',
        'vengexca': '..\\spirexc\\CD\\SPIRIT.cue',
        'whalvoy2': '..\\whalvoy1\\cd\\whalvoy1.cue',
        'WC2DLX': '..\\WC\\cd\\WC.cue'
    }
    if game in unusedCds:
        cue = os.path.join(localGameOutputDir, game, util.localOutputPath(unusedCds[game]))
        cueDir = os.path.dirname(cue)
        cdFiles = [file for file in os.listdir(cueDir) if
                   os.path.splitext(ntpath.basename(cue))[0] == os.path.splitext(file)[0]
                   and os.path.splitext(file)[-1].lower() in ['.ccd', '.sub', '.cue', '.iso', '.img', '.bin']]
        for cdFile in cdFiles:
            logger.log("      remove unused cd file %s" % cdFile)
            os.remove(os.path.join(cueDir, cdFile))


# Creates launch.bat and handles mount and imgmount paths
def batsAndMounts(game, outputDir, localGameOutputDir, logger):
    dosboxBat = open(os.path.join(localGameOutputDir, "dosbox.bat"), 'r')
    launchBat = open(os.path.join(localGameOutputDir, "1_Start.bat"), 'w')
    lines = dosboxBat.readlines()
    for line in lines:
        line = line.lstrip('@ ').rstrip(' \n\r')
        if line.lower() != 'c:' and not line.lower().startswith('path=') and not line.lower().startswith('path ='):
            if line.startswith("imgmount"):
                launchBat.write(convertImgMount(line, game, outputDir, localGameOutputDir, logger))
            elif line.startswith("mount") and not line.lower().startswith('mountain'):
                launchBat.write(convertMount(line, game, outputDir, localGameOutputDir, logger))
            elif line.startswith("boot") and line != 'boots':
                if line == 'boot -l c':
                    launchBat.write('imgset r\n')
                elif line != 'boot' and line != 'boot -l a':
                    launchBat.write(convertBoot(line, game, outputDir, localGameOutputDir, logger))
                else:
                    logger.log('      <ERROR> Impossible to convert "%s" command' % line, logger.ERROR)
                    launchBat.write(line + '\n')
            elif line.lower() in ['d:', 'f:', 'g:', 'h:', 'i:', 'j:', 'k:']:
                launchBat.write('e:\n')
            elif line.lower() == 'call run' or line.lower() == 'call run.bat':
                if game in ['bisle2', 'Blood', 'Carmaged', 'comcon', 'comconra', 'CrypticP', 'lemm3', 'LewLeon',
                            'MechW2', 'rarkani1', 'Resurrec', 'stjudgec']:
                    handleRunBat(game, localGameOutputDir, outputDir, logger)
                launchBat.write(line)
            else:
                launchBat.write(line + '\n')
    # Change imgmount iso command to imgset ide10 cdgames/gamefolder/game.iso
    # Include imgset in the outputDir ?
    # Convert imgmount or mount of floppy to imgset fdd0 /floppy/filename.img
    launchBat.close()
    dosboxBat.close()
    createSetupBat(localGameOutputDir, game)
    createEditBat(localGameOutputDir)
    os.remove(os.path.join(localGameOutputDir, 'dosbox.bat'))


# Treat run.bat command inside game directory
def handleRunBat(game, localGameOutputDir, outputDir, logger):
    runBat = os.path.join(localGameOutputDir, game, 'run.bat')
    if os.path.exists(runBat):
        runFile = open(runBat, 'r')
        runFileClone = open(runBat + '1', 'w')
        # Clone run.bat and only modify imgmount lines
        # Add some hardcoded lines which are impossible to handle
        handled = {
            'imgmount d ".\\cd\\comma2.iso" ".\\cd\\comma1.iso" ".\\cd\\cover3.cue" -t cdrom': 'imgset ide10 "/cd/comcon/comma2.iso"',
            'imgmount d ".\\cd\\cover3.cue" ".\\cd\\comma2.iso" ".\\cd\\comma1.iso" -t cdrom': 'imgset ide10 "/cd/comcon/cover3.cue"',
            'imgmount d ".\\cd\\redal2.iso" ".\\cd\\redal1.iso" ".\\cd\\redal3.iso" ".\\cd\\redal4.iso" -t cdrom':
                'imgset ide10 "/cd/comconra/redal2.iso"',
            'imgmount d ".\\cd\\redal4.iso" ".\\cd\\redal1.iso" ".\\cd\\redal2.iso" ".\\cd\\redal3.iso" -t cdrom':
                'imgset ide10 "/cd/comconra/redal4.iso"',
            'imgmount d ".\\cd\\redal3.iso" ".\\cd\\redal1.iso" ".\\cd\\redal2.iso" ".\\cd\\redal4.iso" -t cdrom':
                'imgset ide10 "/cd/comconra/redal3.iso"'}
        for cmdline in runFile.readlines():
            cmdline = cmdline.lstrip('@ ').rstrip(' \n\r')
            if cmdline.lower().startswith("imgmount "):
                if cmdline not in handled:
                    handled[cmdline] = convertImgMount(cmdline, game, outputDir, localGameOutputDir, logger)
                runFileClone.write(handled[cmdline] + '\n')
            else:
                runFileClone.write(cmdline + '\n')
        runFileClone.close()
        runFile.close()
        # Delete runbat and rename runbat clone to runbat
        os.remove(os.path.join(localGameOutputDir, game, 'run.bat'))
        os.rename(os.path.join(localGameOutputDir, game, 'run.bat1'), os.path.join(localGameOutputDir, game, 'run.bat'))
    else:
        logger.log('    <ERROR> run.bat not found', logger.ERROR)


# Convert imgmount command for MiSTeR
def convertImgMount(line, game, outputDir, localGameOutputDir, logger):
    return handlesFileType(line, 2, game, outputDir, localGameOutputDir, logger)


# Convert mount command for MiSTeR
def convertMount(line, game, outputDir, localGameOutputDir, logger):
    return handlesFileType(line, 2, game, outputDir, localGameOutputDir, logger)


# Convert boot command for MiSTeR
def convertBoot(line, game, outputDir, localGameOutputDir, logger):
    return handlesFileType(line, 1, game, outputDir, localGameOutputDir, logger)


# Determine type of files
def handlesFileType(line, pathPos, game, outputDir, localGameOutputDir, logger):
    params = line.split(' ')
    # TODO Boot command without parameter will crash here, needs to be parsed properly
    path = params[pathPos].replace('"', '')
    if params[0] in ['imgmount', 'mount']:
        if params[-1].rstrip('\n\r ') == 'cdrom' or params[-1].rstrip('\n\r ') == 'iso':
            localPath = locateMountedFiles(path, params[0], game, outputDir, localGameOutputDir)
            misterCommand = convertCD(localPath, game, outputDir, localGameOutputDir, logger, params[1])
            # TODO Handle params[3] to -t to move cds to cd folder (case where multiple cds are mounted)
            # params size > 5 ?
            if len(params) > 5:
                i = 3
                while i < (len(params) - 2):
                    print(params[i])
                    localPath = locateMountedFiles(params[i].replace('"', ''), params[0], game, outputDir,
                                                   localGameOutputDir)
                    # Only move the other CDs
                    convertCD(localPath, game, outputDir, localGameOutputDir, logger, params[1])
                    i = i + 1
            return misterCommand
        elif params[-1].rstrip('\n\r ') == 'floppy':
            localPath = locateMountedFiles(path, params[0], game, outputDir, localGameOutputDir)
            return convertFloppy(localPath, game, outputDir, localGameOutputDir, logger, params[1])
        else:  # Treat default version as cd
            localPath = locateMountedFiles(path, params[0], game, outputDir, localGameOutputDir)
            if params[1].rstrip('\n\r ') == 'c':
                return convertBootDisk(localPath, game, outputDir, localGameOutputDir, logger)
            else:
                return convertCD(localPath, game, outputDir, localGameOutputDir, logger)
    else:  # Boot command
        localPath = locateMountedFiles(path, params[0], game, outputDir, localGameOutputDir)
        return convertFloppy(localPath, game, outputDir, localGameOutputDir, logger, 'a')


# Locate mounted files
def locateMountedFiles(path, command, game, outputDir, localGameOutputDir):
    if platform.system() == 'Windows':
        path = path.replace('/', '\\')

    localPath = util.localOutputPath(os.path.join(localGameOutputDir, path))
    if not os.path.exists(localPath):
        localPath = util.localOutputPath(os.path.join(localGameOutputDir, game, path))
    if not os.path.exists(localPath):
        localPath = util.localOutputPath(os.path.join(outputDir, path))
    if not os.path.exists(localPath):
        localPath = util.localOutputPath(os.path.join(outputDir, game + '.pc', path))
    if not os.path.exists(localPath):
        localPath = util.localOutputPath(os.path.join(outputDir, game + '.pc', game, path))
    return localPath


# Convert cds file
def convertCD(localPath, game, outputDir, localGameOutputDir, logger, letter='d'):
    # Move cds file
    if not os.path.exists(os.path.join(outputDir, 'cd')):
        os.mkdir(os.path.join(outputDir, 'cd'))

    if os.path.isdir(localPath):
        return convertMountedFolder('e', localPath, game, outputDir, localGameOutputDir, logger)
    else:
        # Move cds file
        if not os.path.exists(os.path.join(outputDir, 'cd', game)):
            os.mkdir(os.path.join(outputDir, 'cd', game))

        imgmountDir = os.path.dirname(localPath)

        cdFiles = [file for file in os.listdir(imgmountDir) if
                   os.path.splitext(ntpath.basename(localPath))[0] == os.path.splitext(file)[0]
                   and os.path.splitext(file)[-1].lower() in ['.ccd', '.sub', '.cue', '.iso', '.img', '.bin']]
        for cdFile in cdFiles:
            logger.log("      move %s to %s folder" % (cdFile, 'cd'))
            shutil.move(os.path.join(imgmountDir, cdFile), os.path.join(outputDir, 'cd', game))
        # Move all music files except FLAC an FLA
        musicFiles = [file for file in os.listdir(imgmountDir)
                      if os.path.splitext(file)[-1].lower() in ['.ogg', '.mp3', '.wav']]
        for musicFile in musicFiles:
            logger.log("      move %s to %s folder" % (musicFile, 'cd'))
            shutil.move(os.path.join(imgmountDir, musicFile), os.path.join(outputDir, 'cd', game))
        # Delete all FLAC and FLA files
        flacFiles = [file for file in os.listdir(imgmountDir)
                     if os.path.splitext(file)[-1].lower() in ['.flac', '.fla']]
        for flacFile in flacFiles:
            os.remove(os.path.join(imgmountDir, flacFile))
        # Modify and return command line
        if letter == 'd':
            return 'imgset ide10 "/cd/' + game + '/' + ntpath.basename(localPath) + '"\n'
        else:
            return 'imgset ide11 "/cd/' + game + '/' + ntpath.basename(localPath) + '"\n'


# Convert floppy file
def convertFloppy(localPath, game, outputDir, localGameOutputDir, logger, letter):
    # Move bootable file
    if not os.path.exists(os.path.join(outputDir, 'floppy')):
        os.mkdir(os.path.join(outputDir, 'floppy'))

    if os.path.isdir(localPath):
        return convertMountedFolder(letter, localPath, game, outputDir, localGameOutputDir, logger)
    else:
        if not os.path.exists(os.path.join(outputDir, 'floppy', game)):
            os.mkdir(os.path.join(outputDir, 'floppy', game))
        logger.log("      move %s to %s folder" % (ntpath.basename(localPath), 'floppy'))
        shutil.move(localPath, os.path.join(outputDir, 'floppy', game))
        # Modify and return command line
        return 'imgset fdd0 "/floppy/' + game + '/' + ntpath.basename(localPath) + '"\n'


# Convert bootdisk file
def convertBootDisk(localPath, game, outputDir, localGameOutputDir, logger):
    # Move bootable file
    if not os.path.exists(os.path.join(outputDir, 'bootdisk')):
        os.mkdir(os.path.join(outputDir, 'bootdisk'))

    if os.path.isdir(localPath):
        return convertMountedFolder('c', localPath, game, outputDir, localGameOutputDir, logger)
    else:
        if not os.path.exists(os.path.join(outputDir, 'bootdisk', game)):
            os.mkdir(os.path.join(outputDir, 'bootdisk', game))
        logger.log("      move %s to %s folder" % (ntpath.basename(localPath), 'bootdisk'))
        shutil.move(localPath,
                    os.path.join(outputDir, 'bootdisk', game, os.path.splitext(ntpath.basename(localPath))[0] + '.vhd'))
        # Modify and return command line
        return 'imgset ide00 "/bootdisk/' + game + '/' + os.path.splitext(ntpath.basename(localPath))[
            0] + '.vhd' + '"\n'


# Convert mounted or imgmounted folder
def convertMountedFolder(letter, localPath, game, outputDir, localGameOutputDir, logger):
    if localPath.endswith('\\'):
        localPath = localPath[:-1]
    # TODO basename is not good either, path is lost !! needs reduction of the path instead / missing parts
    logger.log("      subst folder %s as %s:" % (ntpath.basename(localPath), letter))
    return 'subst /d ' + letter + ':\nsubst ' + letter + ': ' + ntpath.basename(localPath)


# Create Setup.bat file
def createSetupBat(localGameOutputDir, game):
    setupBat = open(os.path.join(localGameOutputDir, "3_Setup.bat"), 'w')
    setupBat.write('@echo off\n')
    setupBat.write('cd %s\n' % game)
    setupFiles = [file.lower() for file in os.listdir(os.path.join(localGameOutputDir, game)) if file.lower() in
                  [game.lower(), 'setsound.exe', 'sound.exe', 'sound.com', 'install.exe', 'install.com',
                   'setup.exe', 'setup.com']]
    if len(setupFiles) <= 1 and os.path.exists(os.path.join(localGameOutputDir, game, game)):
        setupBat.write('cd %s\n' % game)
    setupBat.write('\n')
    setupBat.write('IF EXIST setsound.exe goto :sound1\n')
    setupBat.write('IF EXIST sound.exe goto :sound2\n')
    setupBat.write('IF EXIST sound.com goto :sound3\n')
    setupBat.write('IF EXIST install.exe goto :install1\n')
    setupBat.write('IF EXIST install.com goto :install2\n')
    setupBat.write('IF EXIST setup.exe goto :setup1\n')
    setupBat.write('IF EXIST setup.com goto :setup2\n')
    setupBat.write('\n')
    setupBat.write(
        'ECHO No setup files were found for this game.  You will need to manually run the appropriate setup in DOS.\n')
    setupBat.write('pause\n')
    setupBat.write('goto :END\n')
    setupBat.write('\n')
    setupBat.write(':sound1\n')
    setupBat.write('call setsound.exe\n')
    setupBat.write('goto :END\n')
    setupBat.write('\n')
    setupBat.write(':sound2\n')
    setupBat.write('call sound.exe\n')
    setupBat.write('goto :END\n')
    setupBat.write('\n')
    setupBat.write(':sound3\n')
    setupBat.write('call sound.com\n')
    setupBat.write('gotto :END\n')
    setupBat.write('\n')
    setupBat.write(':setup1\n')
    setupBat.write('call setup.exe\n')
    setupBat.write('goto :END\n')
    setupBat.write('\n')
    setupBat.write(':setup2\n')
    setupBat.write('call setup.com\n')
    setupBat.write('goto :END\n')
    setupBat.write('\n')
    setupBat.write(':install1\n')
    setupBat.write('call install.exe\n')
    setupBat.write('goto :END\n')
    setupBat.write('\n')
    setupBat.write(':install2\n')
    setupBat.write('call install.com\n')
    setupBat.write('goto :END\n')
    setupBat.write('\n')
    setupBat.write(':END\n')
    setupBat.write('CLS\n')
    setupBat.close()


# Create Edit.bat file
def createEditBat(localGameOutputDir):
    editBat = open(os.path.join(localGameOutputDir, "4_Edit.bat"), 'w')
    editBat.write('@echo off\nedit 1_Start.bat\n')
    editBat.close()


# Create about.png
def text2png(text, fullpath, color="#FFF", bgcolor="#000", fontfullpath=None, fontsize=13, leftpadding=3,
             rightpadding=3, width=200):
    REPLACEMENT_CHARACTER = u'\uFFFD'
    NEWLINE_REPLACEMENT_STRING = ' ' + REPLACEMENT_CHARACTER + ' '
    font = ImageFont.truetype('DejaVuSans.ttf', 12)
    text = text.replace('\n', NEWLINE_REPLACEMENT_STRING)

    lines = []
    line = u""
    for word in text.split():
        if word == REPLACEMENT_CHARACTER:  # give a blank line
            lines.append(line[1:])  # slice the white space in the begining of the line
            line = u""
            lines.append(u"")  # the blank line
        elif font.getsize(line + ' ' + word)[0] <= (width - rightpadding - leftpadding):
            line += ' ' + word
        else:  # start a new line
            lines.append(line[1:])  # slice the white space in the begining of the line
            line = u""
            # TODO: handle too long words at this point
            line += ' ' + word  # for now, assume no word alone can exceed the line width

    if len(line) != 0:
        lines.append(line[1:])  # add the last line

    line_height = font.getsize(text)[1]
    img_height = line_height * (len(lines) + 1)
    img = Image.new("RGBA", (640, img_height), bgcolor)
    draw = ImageDraw.Draw(img)

    y = 0
    for line in lines:
        draw.text((leftpadding, y), line, color, font=font)
        y += line_height

    img.save(fullpath)
