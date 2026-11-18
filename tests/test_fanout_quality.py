import copy
import unittest
from oci_lenz.quality import edge_conflicts


class FanoutQualityTests(unittest.TestCase):
    def path(self,source,target,points):return {'source':source,'target':target,'network':False,'points':points}

    def test_shared_backend_prefix_across_multiple_bends_is_not_ambiguity(self):
        paths=[self.path('set','a',[(0,0),(0,50),(100,50),(100,100)]),
               self.path('set','b',[(0,0),(0,50),(60,50),(60,100)])]
        nodes={'set':{'kind':'backend_set'},'a':{'kind':'compute'},'b':{'kind':'compute'}}
        original=copy.deepcopy(paths)
        self.assertEqual(edge_conflicts(paths,nodes),{'edge_crossings':0,'edge_overlap_length':0})
        self.assertEqual(paths,original)

    def test_crossing_after_backend_branches_diverge_is_still_counted(self):
        paths=[self.path('set','a',[(0,0),(0,50),(100,50),(100,100)]),
               self.path('set','b',[(0,0),(0,50),(-20,50),(-20,80),(120,80)])]
        nodes={'set':{'kind':'backend_set'},'a':{'kind':'compute'},'b':{'kind':'compute'}}
        self.assertGreater(edge_conflicts(paths,nodes)['edge_crossings'],0)

    def test_similar_geometry_from_different_backend_sets_is_not_exempt(self):
        paths=[self.path('one','a',[(0,0),(0,50),(100,50)]),
               self.path('two','b',[(0,0),(0,50),(60,50)])]
        nodes={k:{'kind':'backend_set' if k in ('one','two') else 'compute'} for k in ('one','two','a','b')}
        self.assertGreater(edge_conflicts(paths,nodes)['edge_overlap_length'],0)

    def test_overlap_after_divergence_is_not_hidden_by_the_shared_prefix(self):
        paths=[self.path('set','a',[(0,0),(0,50),(100,50),(100,100),(200,100)]),
               self.path('set','b',[(0,0),(0,50),(-20,50),(-20,100),(150,100)])]
        nodes={'set':{'kind':'backend_set'},'a':{'kind':'compute'},'b':{'kind':'compute'}}
        self.assertGreater(edge_conflicts(paths,nodes)['edge_overlap_length'],0)

    def test_reversed_native_lb_ownership_uses_the_same_display_owner(self):
        paths=[self.path('a','lb',[(-100,100),(0,100),(0,0)]),
               self.path('b','lb',[(100,100),(0,100),(0,0)])]
        nodes={'lb':{'kind':'lb'},'a':{'kind':'backend_set'},'b':{'kind':'backend_set'}}
        self.assertEqual(edge_conflicts(paths,nodes),{'edge_crossings':0,'edge_overlap_length':0})
