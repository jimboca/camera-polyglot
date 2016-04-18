

ZIP_FILE  = ../profile.zip
XML_FiLES = editor/*.xml nodedef/*.xml 
ZIP_FILES = version.txt nls/*.txt ${XML_FiLES}

all: ${ZIP_FILE}

# sudo apt-get install libxml2-utils libxml2-dev
check:
	xmllint --noout ${XML_FiLES}

${ZIP_FILE}: ${ZIP_FILES}
	zip -r $@ $?
