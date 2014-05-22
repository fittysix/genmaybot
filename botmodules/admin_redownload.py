import tempfile, os, zipfile, urllib.request, urllib.parse, urllib.error, shutil, sys

def redownload_modules(x,y,self,z):

  url = 'https://github.com/KpaBap/genmaybot/zipball/master'
  tmpdir = tempfile.mkdtemp()
  tmpfile = tmpdir+"/bot.zip"


  ### sys.argv[0] contains the name of the script as ran on the command line
  ### os.path.abspath will return the full path to the script regardless of how it was ran
  ### this allows us to figure out where to copy extracted files

  mod_dir = os.path.abspath(sys.argv[0])[0:-(len(sys.argv[0]))] + "botmodules"

  try:
    os.stat(mod_dir)
  except:
    return "Please modify redownload.py to contain the correct module path"

  try:
    urllib.request.urlretrieve(url, tmpfile)
  except:
    return "There was an error downloading the source code."

  zip = zipfile.ZipFile(tmpfile,'r')
  for srcfile in zip.namelist():
    if srcfile.find("/botmodules/") != -1:
      try:
        zip.extract(srcfile,tmpdir)
      except:
        return "Something went wrong while unzipping the source code file"
      if srcfile[-3:] == ".py":
        shutil.copy(tmpdir+"/"+srcfile, mod_dir)

  zip.close()
  shutil.rmtree(tmpdir)
  self.loadmodules()
  self.load_config()
  return "The bot has redownloaded itself from GitHub and reloaded any changed modules"

redownload_modules.admincommand = "redownload"


