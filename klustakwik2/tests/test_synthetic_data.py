'''
Test clustering performance on synthetic dataset.
'''

from numpy import *
from klustakwik2 import *
from numpy.testing import assert_raises, assert_array_almost_equal, assert_array_equal
from nose import with_setup
from nose.tools import nottest
from numpy.random import randint, rand, randn
from six.moves import range
import unittest

@nottest
def test_approximately_well_clustered(clusters, num_clusters, cluster_size, fraction=0.02):
    b = bincount(clusters)
    assert b[0]<=fraction*cluster_size
    assert b[1]<=fraction*cluster_size
    dominant_clusters = []
    for i in range(num_clusters):
        cur_clusters = clusters[i*cluster_size:(i+1)*cluster_size]
        b = bincount(cur_clusters)
        dc = argmax(b)
        dominant_clusters.append(dc)
        assert cluster_size-b[dc]<=fraction*cluster_size
    assert len(dominant_clusters)==len(unique(dominant_clusters)) 
    

@nottest
def generate_synthetic_data(num_features, spikes_per_centre, centres, save_to_fet=None):
    '''
    Generates data that comes from a distribution with multiple centres. centres is a list of
    tuples (fet_mean, fet_std, fmask_mean, fmask_std) and features and masks are generated via
    normal random numbers (fmask is clipped between 0 and 1).

    TODO: data generated by this isn't normalised in [0,1]
    '''
    fet = []
    fmask = []
    offsets = []
    unmasked = []
    n = 0
    num_spikes = len(centres)*spikes_per_centre
    offsets = [n]
    fsum = zeros(num_features)
    fsum2 = zeros(num_features)
    nsum = zeros(num_features)
    if save_to_fet is not None:
        fetfile = open(save_to_fet+'.fet.1', 'wt')
        fmaskfile = open(save_to_fet+'.fmask.1', 'wt')
        fetfile.write('%d\n' % num_features)
        fmaskfile.write('%d\n' % num_features)
    for c, s, fmc, fms in centres:
        c = array(c, dtype=float)
        s = array(s, dtype=float)
        fmc = array(fmc, dtype=float)
        fms = array(fms, dtype=float)
        for i in range(spikes_per_centre):
            f = randn(num_features)*s+c
            fm = clip(randn(num_features)*fms+fmc, 0, 1)
            if save_to_fet is not None:
                fetfile.write(' '.join(map(str, f))+'\n')
                fmaskfile.write(' '.join(map(str, fm))+'\n')
            u, = (fm>0).nonzero()
            m, = (fm==0).nonzero()
            u = array(u, dtype=int)
            fet.append(f[u])
            fmask.append(fm[u])
            unmasked.append(u)
            n += len(u)
            offsets.append(n)
            fsum[m] += f[m]
            fsum2[m] += f[m]**2
            nsum[m] += 1
    fet = hstack(fet)
    fmask = hstack(fmask)
    unmasked = hstack(unmasked)
    offsets = array(offsets)
    return RawSparseData(fsum/nsum, fsum2/nsum-(fsum/nsum)**2,
                         fet, fmask, unmasked, offsets).to_sparse_data()


def test_synthetic_2d_trivial():
    '''
    This is the most trivial clustering problem, two well separated clusters in 2D with almost
    no noise and perfect starting masks. All the algorithm has to do is not do anything. We
    therefore test that it gives perfect results.
    '''
    data = generate_synthetic_data(2, 100, [
       # fet mean, fet var,      fmask mean, fmask var
        ((1, 0),   (0.01, 0.01), (1, 0),     (0.0, 0.0)),
        ((0, 1),   (0.01, 0.01), (0, 1),     (0.0, 0.0)),
        ])
    kk = KK(data, points_for_cluster_mask=1e-100, num_starting_clusters=10)
    kk.cluster_mask_starts()
    test_approximately_well_clustered(kk.clusters, 2, 100)


def test_synthetic_2d_easy():
    '''
    In this test, there is a small amount of variance in both the masks and the features.
    Note that if you put the average mask at 1 instead of 0.5 it fails because the 'corrected'
    data will be non-Gaussian (as it gets clipped between 0 and 1). Similarly, if you put the noise
    in the data as 0 it doesn't work because you get singular matrices.
    '''
    data = generate_synthetic_data(2, 100, [
        ((1, 0), (0.01,)*2, (0.5, 0), (0.01, 0.0)),
        ((0, 1), (0.01,)*2, (0, 0.5), (0.0, 0.01)),
        ])
    kk = KK(data, points_for_cluster_mask=1e-100, num_starting_clusters=10)
    kk.cluster_mask_starts()
    test_approximately_well_clustered(kk.clusters, 2, 100)


def test_synthetic_4d_easy():
    data = generate_synthetic_data(4, 1000, [
        ((1, 1, 0, 0), (0.1,)*4, (1.5, 0.5, 0, 0), (0.05, 0.05, 0, 0)),
        ((0, 1, 1, 0), (0.1,)*4, (0, 0.5, 1.5, 0), (0, 0.05, 0.05, 0)),
        ((0, 0, 1, 1), (0.1,)*4, (0, 0, 0.5, 1.5), (0, 0, 0.05, 0.05)),
        ((1, 0, 0, 1), (0.1,)*4, (1.5, 0, 0, 1.5), (0.05, 0, 0, 0.05)),
        ])
    kk = KK(data, points_for_cluster_mask=1e-100, num_starting_clusters=20)
    kk.cluster_mask_starts()
    test_approximately_well_clustered(kk.clusters, 4, 1000)


def test_synthetic_4d_trivial():
    data = generate_synthetic_data(4, 1000, [
        ((1, 1, 0, 0), (0.1,)*4, (1.5, 0.5, 0, 0), (0,)*4),
        ((0, 1, 1, 0), (0.1,)*4, (0, 0.5, 1.5, 0), (0,)*4),
        ((0, 0, 1, 1), (0.1,)*4, (0, 0, 0.5, 1.5), (0,)*4),
        ((1, 0, 0, 1), (0.1,)*4, (1.5, 0, 0, 1.5), (0,)*4),
        ])
    kk = KK(data, points_for_cluster_mask=1e-100, num_starting_clusters=20)
    kk.cluster_mask_starts()
    test_approximately_well_clustered(kk.clusters, 4, 1000)


@unittest.skip("Tmporarily disabled until we work out why cycles are happening here")
def test_synthetic_4d_easy_non_gaussian():
    data = generate_synthetic_data(4, 1000, [
        ((1, 1, 0, 0), (0.1,)*4, (1.5, 0.5, 0, 0), (0.05, 0.05, 0.01, 0)),
        ((0, 1, 1, 0), (0.1,)*4, (0, 0.5, 1.5, 0), (0, 0.05, 0.05, 0.01)),
        ((0, 0, 1, 1), (0.1,)*4, (0, 0, 0.5, 1.5), (0.01, 0, 0.05, 0.05)),
        ((1, 0, 0, 1), (0.1,)*4, (1.5, 0, 0, 1.5), (0.05, 0, 0.01, 0.05)),
        ])
    # no space for error, so we set quick steps off
    kk = KK(data, full_step_every=1, points_for_cluster_mask=1e-100, num_starting_clusters=20)
    kk.cluster_mask_starts()
    test_approximately_well_clustered(kk.clusters, 4, 1000)

def test_splitting():
    data = generate_synthetic_data(4, 1000, [
        ((1, 1, 0, 0), (0.1,)*4, (1.5, 0.5, 0, 0), (0.05, 0.05, 0, 0)),
        ((0, 1, 1, 0), (0.1,)*4, (0, 0.5, 1.5, 0), (0, 0.05, 0.05, 0)),
        ((0, 0, 1, 1), (0.1,)*4, (0, 0, 0.5, 1.5), (0, 0, 0.05, 0.05)),
        ((1, 0, 0, 1), (0.1,)*4, (1.5, 0, 0, 1.5), (0.05, 0, 0, 0.05)),
        ])
    kk = KK(data, points_for_cluster_mask=1e-100, num_starting_clusters=20,
            split_every=1)
    kk.cluster_mask_starts()


if __name__=='__main__':
#     console_log_level('debug')
    for _ in range(100):
        test_synthetic_2d_trivial()
        test_synthetic_2d_easy()
        test_synthetic_4d_easy()
        test_synthetic_4d_trivial()
        test_synthetic_4d_easy_non_gaussian()
        test_splitting()