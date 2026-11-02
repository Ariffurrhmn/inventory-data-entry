"""Synthetic geometry checks; these are software tests, not extraction accuracy."""
import unittest
from PIL import Image,ImageDraw
from localization import locate,montage,inverse_affine
class LocalizationTests(unittest.TestCase):
    def test_blank_has_no_invented_grid(self):
        _,layout,_=locate(Image.new('RGB',(800,1000),'white'))
        self.assertEqual(layout['tables'],[])
    def test_ruled_grid_is_localized_without_coordinates(self):
        im=Image.new('RGB',(800,1000),'white');d=ImageDraw.Draw(im)
        for x in [100,300,700]: d.line((x,300,x,600),fill='black',width=3)
        for y in [300,400,500,600]: d.line((100,y,700,y),fill='black',width=3)
        norm,layout,_=locate(im)
        self.assertEqual(len(layout['tables']),1)
        self.assertEqual(len(layout['tables'][0]['rows']),3)
        self.assertEqual([len(r) for r in layout['tables'][0]['rows']],[2,2,2])
        view,mapping=montage(norm,layout['tables']);self.assertEqual(len(mapping),6)
        self.assertGreater(view.width,0)
    def test_inverse_uses_actual_rounded_dimensions(self):
        matrix=inverse_affine((803,1001),.6,0)
        self.assertAlmostEqual(matrix[0][0],803/round(803*.6))
        self.assertAlmostEqual(matrix[1][1],1001/round(1001*.6))
    def test_inverse_identity_and_scale(self):
        self.assertEqual(inverse_affine((800,1000),1,0),[[1.0,-0.0,0.0],[0.0,1.0,0.0]])
        self.assertEqual(inverse_affine((800,1000),.5,0),[[2.0,-0.0,0.0],[0.0,2.0,0.0]])
if __name__=='__main__': unittest.main()
