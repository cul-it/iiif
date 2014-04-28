"""
Implementation of IIIF Image API manipulations using the Python Image Library

Uses the Python Image Library (PIL) for in-python manipulation:
http://www.pythonware.com/products/pil/index.htm
"""

import re
import os
import os.path
import subprocess
import tempfile

from PIL import Image

from error import IIIFError
from request import IIIFRequest
from manipulator import IIIFManipulator

class IIIFManipulatorPIL(IIIFManipulator):
    """Module to manipulate and image according to iiif rules

    All exceptions are raise as Error objects which directly
    determine the HTTP response.
    """

    tmpdir = '/tmp'
    filecmd = None
    pnmdir = None

    def __init__(self):
        super(IIIFManipulatorPIL, self).__init__()
        # Does not support jp2 output
        self.complianceLevel="http://iiif.example.org/compliance/level/0"
        self.outtmp = None

    def do_first(self):
        """Create PIL object from input image file
        """
        print "src=%s" % (self.srcfile)
        try:
            self.image=Image.open(self.srcfile)
            self.image.load()
        except Exception as e:
            raise IIIFError(text=("PIL Image.open(%s) barfed: %s",(self.srcfile,str(e))))
        (self.width,self.height)=self.image.size

    def do_region(self):
        (x,y,w,h)=self.region_to_apply()
        if (x is None):
            print "region: full (nop)"
        else:
            print "region: (%d,%d,%d,%d)" % (x,y,w,h)
            self.image = self.image.crop( (x,y,x+w,y+h) )
            self.width = w
            self.height = h

    def do_size(self):
        (w,h)=self.size_to_apply()
        if (w is None):
            print "size: no scaling (nop)"
        else:
            print "size: scaling to (%d,%d)" % (w,h)
            self.image = self.image.resize( (w,h) )
            self.width = w
            self.height = h

    def do_rotation(self):
        rot=self.rotation_to_apply()
        if (rot==0.0):
            print "rotation: no rotation (nop)"
        else:
            print "rotation: by %f degrees clockwise" % (rot)
            self.image = self.image.rotate( -rot, expand=True )

    def do_quality(self):
        quality=self.quality_to_apply()
        if (quality == 'grey'):
            print "quality: grey"
        elif (quality == 'bitonal'):
            print "quality: bitonal"
        else:
            print "quality: quality (nop)"

    def do_format(self):
        # assume tiling apps want jpg...
        fmt = ( 'jpg' if (self.request.format is None) else self.request.format)
        if (fmt == 'png'):
            print "format: png"
            self.mime_type="image/png"
            self.output_format=fmt
            format = 'png'
        elif (fmt == 'jpg'):
            print "format: jpg"
            self.mime_type="image/jpeg"
            self.output_format=fmt
            format = 'jpeg';
        else:
            raise IIIFError(code=415, parameter='format',
                           text="Unsupported output file format (%s), only png,jpg are supported."%(fmt))

        if (self.outfile is None):
            # Create temp
            f = tempfile.NamedTemporaryFile(delete=False)
            self.outfile=f.name
            self.outtmp=f.name
            self.image.save(f,format='png')
        else:
            # Save to specified location
            self.image.save(self.outfile,format='jpeg')

    def cleanup(self):
        if (self.outtmp is not None):
            try:
                os.unlink(self.outtmp)
            except OSError as e:
                # FIXME - should log warning when we have logging...
                pass
