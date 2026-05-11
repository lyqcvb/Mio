FROM tindy2013/subconverter:latest

COPY replacements/config/ /base/config/
COPY replacements/snippets/ /base/snippets/

EXPOSE 25500
