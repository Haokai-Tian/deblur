# -----------------------------------------------------------------------------
# Copyright (c) 2015, The Deblur Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from io import StringIO
from os.path import join, dirname, abspath

import skbio
import numpy as np

from deblur.sequence import Sequence
from deblur.workflow import sequence_generator
from deblur.deblurring import get_sequences, deblur, get_default_error_profile


class DeblurringTests(TestCase):
    def setUp(self):
        self.seqs = [("151_9240;size=170;", "---tagggcaagactccatggt-----"),
                     ("151_6640;size=1068;", "---cggaggcgagatgcgtggt-----"),
                     ("151_64278;size=200;", "---tactagcaagattcctggt-----"),
                     ("151_4447;size=1812;", "---aggatgcgagatgcgtggt-----"),
                     ("151_14716;size=390;", "---gagtgcgagatgcgtggtg-----"),
                     ("151_3288;size=1337;", "---ggatgcgagatgcgtggtg-----"),
                     ("151_41690;size=157;", "---agg-gcgagattcctagtgg----"),
                     ("151_5155;size=998;", "---gaggatgcgagatgcgtgg-----"),
                     ("151_527;size=964;", "---acggaggatgatgcgcggt-----"),
                     ("151_5777;size=305;", "---ggagtgcaagattccaggt-----")]
        self.test_data_dir = join(dirname(abspath(__file__)), 'data')

    def test_get_default_error_profile(self):
        goodprofile = [1, 0.06, 0.02, 0.02, 0.01,
                       0.005, 0.005, 0.005, 0.001, 0.001,
                       0.001, 0.0005]
        self.assertEqual(goodprofile, get_default_error_profile())

    def test_get_sequences_error_real_length(self):
        seqs = [("151_9240;size=170;", "----tagggcaagactccatg-----"),
                ("151_6640;size=1068;", "--acggaggcga-atgcgtggt----"),
                ("151_64278;size=200;", "---tactagcaagattcctgg-----")]

        with self.assertRaises(ValueError):
            get_sequences(seqs)

    def test_get_sequences_error_length(self):
        seqs = [("151_9240;size=170;", "----tagggcaagactccatg----"),
                ("151_6640;size=1068;", "--acggaggcgagatgcgtggt----"),
                ("151_64278;size=200;", "---tactagcaagattcctgg-----")]

        with self.assertRaises(ValueError):
            get_sequences(seqs)

    def test_get_sequences_empty_file(self):
        gen = skbio.read(join(self.test_data_dir, 'seqs_empty.fasta'),
                         format='fasta')
        self.assertEqual(get_sequences(gen), None)

    def test_get_sequences_error_empty(self):
        self.assertIsNone(get_sequences([]))

    def test_deblur_noseqs(self):
        """If no sequences supplied, need to return None
        """
        res = deblur([])
        self.assertEqual(res, None)

    def test_get_sequences(self):
        exp_seqs = [
            Sequence("151_4447;size=1812;", "---aggatgcgagatgcgtggt-----"),
            Sequence("151_3288;size=1337;", "---ggatgcgagatgcgtggtg-----"),
            Sequence("151_6640;size=1068;", "---cggaggcgagatgcgtggt-----"),
            Sequence("151_5155;size=998;", "---gaggatgcgagatgcgtgg-----"),
            Sequence("151_527;size=964;", "---acggaggatgatgcgcggt-----"),
            Sequence("151_14716;size=390;", "---gagtgcgagatgcgtggtg-----"),
            Sequence("151_5777;size=305;", "---ggagtgcaagattccaggt-----"),
            Sequence("151_64278;size=200;", "---tactagcaagattcctggt-----"),
            Sequence("151_9240;size=170;", "---tagggcaagactccatggt-----"),
            Sequence("151_41690;size=157;", "---agg-gcgagattcctagtgg----")]
        obs_seqs = get_sequences(self.seqs)
        self.assertEqual(obs_seqs, exp_seqs)

    def test_deblur_toy_example(self):
        seqs_f = StringIO(TEST_SEQS_1)
        obs = deblur(sequence_generator(seqs_f))
        exp = [
            Sequence("E.Coli;size=1000;",
                     "tacggagggtgcaagcgttaatcggaattactgggcgtaaagcgcacgcaggcggt"
                     "ttgttaagtcagatgtgaaatccccgggctcaacctgggaactgcatctgatactg"
                     "gcaagcttgagtctcgtagaggggggcagaattccag")]

        self.assertEqual(obs, exp)

    def test_deblur(self):
        seqs_f = StringIO(TEST_SEQS_2)

        obs = deblur(sequence_generator(seqs_f))
        exp = [
            Sequence("E.Coli-999;size=720;",
                     "tacggagggtgcaagcgttaatcggaattactgggcgtaaagcgcacgcaggcggt"
                     "ttgttaagtcagatgtgaaatccccgggctcaacctgggaactgcatctgatactg"
                     "gcaagcttgagtctcgtagaggggggcagaattccag")]

        self.assertEqual(obs, exp)

    def test_deblur_indel(self):
        """Test if also removes indel sequences
        """
        seqs_f = StringIO(TEST_SEQS_2)

        # add the MSA for the indel
        seqs = sequence_generator(seqs_f)
        newseqs = []
        for chead, cseq in seqs:
            tseq = cseq[:10] + '-' + cseq[10:]
            newseqs.append((chead, tseq))

        # now add a sequence with an A insertion at the expected freq. (30 < 0.02 * (720 / 0.47) where 0.47 is the mod_factor) so should be removed
        cseq = newseqs[0][1]
        tseq = cseq[:10] + 'A' + cseq[11:-1] + '-'
        chead = '>indel1-read;size=30;'
        newseqs.append((chead, tseq))

        # and add a sequence with an A insertion but at higher freq. (not expected by indel upper bound - (31 > 0.02 * (720 / 0.47) so should not be removed)
        cseq = newseqs[0][1]
        tseq = cseq[:10] + 'A' + cseq[11:-1] + '-'
        chead = '>indel2-read;size=31;'
        newseqs.append((chead, tseq))

        obs = deblur(newseqs)

        # remove the '-' (same as in launch_workflow)
        for s in obs:
            s.sequence = s.sequence.replace('-', '')

        # the expected output
        exp = [
            Sequence("E.Coli-999;size=720;",
                     "tacggagggtgcaagcgttaatcggaattactgggcgtaaagcgcacgcaggcggt"
                     "ttgttaagtcagatgtgaaatccccgggctcaacctgggaactgcatctgatactg"
                     "gcaagcttgagtctcgtagaggggggcagaattccag")]
        # make sure we get 2 sequences as output - the original and the indel2 (too many reads for the expected indel probabilty)
        self.assertEqual(len(obs), 2)
        # and that it is the correct sequence
        self.assertEqual(obs[0].sequence, exp[0].sequence)
        self.assertEqual(obs[1].label, '>indel2-read;size=31;')

    def test_deblur_with_non_default_error_profile(self):
        error_dist = [1, 0.05, 0.000005, 0.000005, 0.000005, 0.000005,
                      0.0000025, 0.0000025, 0.0000025, 0.0000025, 0.0000025,
                      0.0000005, 0.0000005, 0.0000005, 0.0000005]
        seqs_f = StringIO(TEST_SEQS_2)

        obs = deblur(sequence_generator(seqs_f), error_dist=error_dist)
        exp = [
            Sequence("E.Coli-999;size=720;",
                     "tacggagggtgcaagcgttaatcggaattactgggcgtaaagcgcacgcaggcggt"
                     "ttgttaagtcagatgtgaaatccccgggctcaacctgggaactgcatctgatactg"
                     "gcaagcttgagtctcgtagaggggggcagaattccag")]

        self.assertEqual(obs, exp)

        error_dist = np.array(
            [1, 0.06, 0.02, 0.02, 0.01,
             0.005, 0.005, 0.005, 0.001,
             0.001, 0.001, 0.0005])
        seqs_f = StringIO(TEST_SEQS_2)
        obs = deblur(sequence_generator(seqs_f), error_dist=error_dist)
        exp = [
            Sequence("E.Coli-999;size=720;",
                     "tacggagggtgcaagcgttaatcggaattactgggcgtaaagcgcacgcaggcggt"
                     "ttgttaagtcagatgtgaaatccccgggctcaacctgggaactgcatctgatactg"
                     "gcaagcttgagtctcgtagaggggggcagaattccag")]

        self.assertEqual(obs, exp)


TEST_SEQS_1 = """>E.Coli;size=1000;
tacggagggtgcaagcgttaatcggaattactgggcgtaaagcgcacgcaggcggtttgt
taagtcagatgtgaaatccccgggctcaacctgggaactgcatctgatactggcaagctt
gagtctcgtagaggggggcagaattccag
>Error;size=3;
aacggagggtgcaagcgttaatcggaattactgggcgtaaagcgcacgcaggcggtttgt
taagtcagatgtgaaatccccgggctcaacctgggaactgcatctgatactggcaagctt
gagtctcgtagaggggggcagaattccag
"""


TEST_SEQS_2 = """>E.Coli-999;size=720;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-781;size=5;
TGCGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-987;size=4;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGGCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-861;size=3;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCATGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-791;size=3;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACACAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-832;size=3;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGATTTCCAG
>E.Coli-476;size=3;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAAGCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-633;size=3;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CTGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-894;size=3;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCAAG
>E.Coli-702;size=3;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAAATCCAG
>E.Coli-986;size=3;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGACGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-991;size=3;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGGTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-975;size=3;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGTCAGAATTCCAG
>E.Coli-670;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTCGAGGGGGGCAGAATTCCAG
>E.Coli-709;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGCGGCAGAATTCCAG
>E.Coli-640;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCCCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-831;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAC
>E.Coli-663;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTATCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-645;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCCTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-799;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTTCAG
>E.Coli-807;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGATTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-795;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCGTCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-785;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGAGGGCAGAATTCCAG
>E.Coli-743;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGGATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-737;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATTTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-749;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTGCAG
>E.Coli-818;size=2;
TCCGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-636;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGAAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-235;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCACAATTCCAG
>E.Coli-228;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGATTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-311;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTTGAGGGGGGCAGAATTCCAG
>E.Coli-393;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATATGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-336;size=2;
TACGGAGGGTGCAAGAGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-190;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTGTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-66;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGCCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-198;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAAGGGGGCAGAATTCCAG
>E.Coli-225;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCTAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-216;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGGAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-555;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCGGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-538;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGTCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-561;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CAGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-615;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAAACC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-604;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGAGGGGCAGAATTCCAG
>E.Coli-498;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
TCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-455;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGCCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-507;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTACATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-519;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGAAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-511;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCTG
>E.Coli-983;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGTGGGGGGCAGAATTCCAG
>E.Coli-968;size=2;
TACGGAGGGTGGAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-997;size=2;
TACGGAGGGTGCAAGCCTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-1000;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCTCGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-883;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCACCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-911;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGGACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-963;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACCGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-941;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATGCTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-932;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGGAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-915;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCGACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-917;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACAGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
>E.Coli-838;size=2;
TACGGAGGGTGCAAGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGACAGAATTCCAG
>E.Coli-851;size=2;
TACGGAGGGTGCATGCGTTAATCGGAATTACTGGGCGTAAAGCGCACGCAGGCGGTTTGTTAAGTCAGATGTGAAATCC
CCGGGCTCAACCTGGGAACTGCATCTGATACTGGCAAGCTTGAGTCTCGTAGAGGGGGGCAGAATTCCAG
"""

if __name__ == '__main__':
    main()
