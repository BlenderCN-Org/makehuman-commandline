<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:fo="http://www.w3.org/1999/XSL/Format" xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">

  <xsl:template match="li">
    <text:list-item>
      <text:p text:style-name="listpara"><xsl:apply-templates /></text:p>
    </text:list-item>
  </xsl:template>

</xsl:stylesheet>
