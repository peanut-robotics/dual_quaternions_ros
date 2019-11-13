import os
from unittest import TestCase
from dual_quaternions_ros import DualQuaternion
import numpy as np
import quaternion

import geometry_msgs.msg


class TestDualQuaternion(TestCase):

    def setUp(self):
        self.unit_dq = DualQuaternion.identity()
        self.random_dq = DualQuaternion.from_quat_pose_array(np.array([1,2,3,4,5,6,7]))
        self.other_random_dq = DualQuaternion.from_quat_pose_array(np.array([0.2,0.1,0.3,0.07,1.2,0.9]))
        self.normalized_dq = self.random_dq.normalized()

    def test_creation(self):
        # from dual quaternion array: careful, need to supply a normalized DQ
        dql = np.array([0.7071067811, 0.7071067811, 0, 0, -3.535533905, 3.535533905, 1.767766952, -1.767766952])
        dq1 = DualQuaternion.from_dq_array(dql)
        dq2 = DualQuaternion.from_dq_array(dql)
        self.assertEqual(dq1, dq2)
        # from quaternion + translation array
        dq3 = DualQuaternion.from_quat_pose_array(np.array([1, 2, 3, 4, 5, 6, 7]))
        dq4 = DualQuaternion.from_quat_pose_array([1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(dq3, dq4)
        # from ROS pose
        ros_pose = geometry_msgs.msg.Pose()
        ros_pose.orientation.w = 1.
        dq5 = DualQuaternion.from_ros_pose(ros_pose)
        self.assertEqual(dq5, self.unit_dq)
        self.assertEqual(dq5.ros_pose(), ros_pose)
        # from ROS transform
        ros_transform = geometry_msgs.msg.Transform()
        ros_transform.rotation.w = 1.
        dq6 = DualQuaternion.from_ros_transform(ros_transform)
        self.assertEqual(dq5, dq6)
        self.assertEqual(dq6.ros_transform(), ros_transform)
        # from homogeneous transformation matrix
        T = np.array([[1, 0, 0, 2], [0, 1, 0, 3], [0, 0, 1, 1], [0, 0, 0, 1]])
        dq7 = DualQuaternion.from_homogeneous_matrix(T)
        self.assertEqual(dq7.q_r, quaternion.one)
        self.assertEqual(dq7.translation(), [2, 3, 1])
        try:
            np.testing.assert_array_almost_equal(dq7.homogeneous_matrix(), T)
        except AssertionError as e:
            self.fail(e)
        # from a point
        dq8 = DualQuaternion.from_translation_vector([4, 6, 8])
        self.assertEqual(dq8.translation(), [4, 6, 8])

    def test_unit(self):
        q_r_unit = np.quaternion(1, 0, 0, 0)
        q_d_zero = np.quaternion(0, 0, 0, 0)
        unit_dq = DualQuaternion(q_r_unit, q_d_zero)
        self.assertEqual(self.unit_dq, unit_dq)
        # unit dual quaternion multiplied with another unit quaternion should yield unit
        self.assertEqual(self.unit_dq * self.unit_dq, self.unit_dq)

    def test_add(self):
        dq1 = DualQuaternion.from_translation_vector([4, 6, 8])
        dq2 = DualQuaternion.from_translation_vector([1, 2, 3])
        sum = dq1 + dq2
        self.assertEqual(sum.q_d, np.quaternion(0., 2.5, 4., 5.5))

    def test_mult(self):
        # quaternion multiplication. Compare with homogeneous transformation matrices
        theta1 = np.pi / 180 * 20  # 20 deg
        T_pure_rot = np.array([[1., 0., 0., 0.],
                               [0., np.cos(theta1), -np.sin(theta1), 0.],
                               [0., np.sin(theta1), np.cos(theta1), 0.],
                               [0., 0., 0., 1.]])
        dq_pure_rot = DualQuaternion.from_homogeneous_matrix(T_pure_rot)
        T_pure_trans = np.array([[1., 0., 0., 1.],
                                 [0., 1., 0., 2.],
                                 [0., 0., 1., 3.],
                                 [0., 0., 0., 1.]])
        dq_pure_trans = DualQuaternion.from_homogeneous_matrix(T_pure_trans)

        T_double_rot = np.dot(T_pure_rot, T_pure_rot)
        dq_double_rot = dq_pure_rot * dq_pure_rot
        try:
            np.testing.assert_array_almost_equal(T_double_rot, dq_double_rot.homogeneous_matrix())
        except AssertionError as e:
            self.fail(e)

        T_double_trans = np.dot(T_pure_trans, T_pure_trans)
        dq_double_trans = dq_pure_trans * dq_pure_trans
        try:
            np.testing.assert_array_almost_equal(T_double_trans, dq_double_trans.homogeneous_matrix())
        except AssertionError as e:
            self.fail(e)

        # composed: trans and rot
        T_composed = np.dot(T_pure_rot, T_pure_trans)
        dq_composed = dq_pure_rot * dq_pure_trans
        dq_composed = dq_pure_rot * dq_pure_trans
        try:
            np.testing.assert_array_almost_equal(T_composed, dq_composed.homogeneous_matrix())
        except AssertionError as e:
            self.fail(e)

    def test_div(self):
        try:
            np.testing.assert_array_almost_equal((self.random_dq/self.random_dq).dq_array(),
                                                 self.unit_dq.dq_array())
            np.testing.assert_array_almost_equal((self.random_dq/self.unit_dq).dq_array(),
                                                 self.random_dq.dq_array())
        except AssertionError as e:
            self.fail(e)

    def test_inverse(self):
        # use known matrix inversion
        T_1_2 = np.array([[0, 1, 0, 2], [-1, 0, 0, 4], [0, 0, 1, 6], [0, 0, 0, 1]])
        T_2_1 = np.array([[0, -1, 0, 4], [1, 0, 0, -2], [0, 0, 1, -6], [0, 0, 0, 1]])
        dq_1_2 = DualQuaternion.from_homogeneous_matrix(T_1_2)
        dq_2_1 = DualQuaternion.from_homogeneous_matrix(T_2_1)

        try:
            np.testing.assert_array_almost_equal(dq_2_1.homogeneous_matrix(), dq_1_2.inverse().homogeneous_matrix())
        except AssertionError as e:
            self.fail(e)

    def test_equal(self):
        self.assertTrue(self.unit_dq == DualQuaternion.identity())
        self.assertTrue(self.unit_dq == DualQuaternion(-np.quaternion(1, 0, 0, 0), -np.quaternion(0, 0, 0, 0)))
        self.assertFalse(self.unit_dq == DualQuaternion(np.quaternion(1, 0, 0, 1), -np.quaternion(0, 0, 0, 0)))
        theta1 = np.pi / 180 * 20  # 20 deg
        T_pure_rot = np.array([[1., 0., 0., 0.],
                               [0., np.cos(theta1), -np.sin(theta1), 0.],
                               [0., np.sin(theta1), np.cos(theta1), 0.],
                               [0., 0., 0., 1.]])
        dq_pure_rot = DualQuaternion.from_homogeneous_matrix(T_pure_rot)
        # manually flip sign on terms
        dq_pure_rot.q_r = - dq_pure_rot.q_r
        dq_pure_rot.q_d = - dq_pure_rot.q_d
        try:
            np.testing.assert_array_almost_equal(dq_pure_rot.homogeneous_matrix(), T_pure_rot)
        except AssertionError as e:
            self.fail(e)
        dq_pure_rot.q_d = - dq_pure_rot.q_d
        try:
            np.testing.assert_array_almost_equal(dq_pure_rot.homogeneous_matrix(), T_pure_rot)
        except AssertionError as e:
            self.fail(e)
        dq_pure_rot.q_r = - dq_pure_rot.q_r
        try:
            np.testing.assert_array_almost_equal(dq_pure_rot.homogeneous_matrix(), T_pure_rot)
        except AssertionError as e:
            self.fail(e)

    def test_str_repr_is_string(self):
        # test that __str__ and __repr__ are working
        self.assertTrue(isinstance(repr(self.unit_dq), basestring))
        self.assertTrue(isinstance(self.unit_dq.__str__(), basestring))

    def test_quaternion_conjugate(self):
        dq = self.normalized_dq * self.normalized_dq.quaternion_conjugate()
        # a normalized quaternion multiplied with its quaternion conjugate should yield unit dual quaternion
        self.assertTrue(dq == DualQuaternion.identity())

        # test that the conjugate corresponds to the inverse of it's matrix representation
        matr = self.normalized_dq.homogeneous_matrix()
        inv = np.linalg.inv(matr)
        self.assertTrue(DualQuaternion.from_homogeneous_matrix(inv) == self.normalized_dq.quaternion_conjugate())

        # (dq1 @ dq2)* ?= dq2* @ dq1*
        res1 = (self.random_dq * self.other_random_dq).quaternion_conjugate()
        res2 = self.other_random_dq.quaternion_conjugate() * self.random_dq.quaternion_conjugate()
        self.assertTrue(res1 == res2)

    def test_homogeneous_conversion(self):
        # 1. starting from a homogeneous matrix
        theta1 = np.pi/2  # 90 deg
        trans = [10., 5., 0.]
        H1 = np.array([[1., 0., 0., trans[0]],
                     [0., np.cos(theta1), -np.sin(theta1), trans[1]],
                     [0., np.sin(theta1), np.cos(theta1), trans[2]],
                     [0., 0., 0., 1.]])
        # check that if we convert to DQ and back to homogeneous matrix, we get the same result
        double_conv1 = DualQuaternion.from_homogeneous_matrix(H1).homogeneous_matrix()
        try:
            np.testing.assert_array_almost_equal(H1, double_conv1)
        except AssertionError as e:
            self.fail(e)
        # check that dual quaternions are also equal
        dq1 = DualQuaternion.from_homogeneous_matrix(H1)
        dq_double1 = DualQuaternion.from_homogeneous_matrix(double_conv1)
        self.assertTrue(dq1 == dq_double1)

        # 2. starting from a DQ
        dq_trans = DualQuaternion.from_translation_vector([10, 5, 0])
        dq_rot = DualQuaternion.from_dq_array([np.cos(theta1 / 2), np.sin(theta1 / 2), 0, 0, 0, 0, 0, 0])
        dq2 = dq_trans * dq_rot
        # check that this is the same as the previous DQ
        self.assertTrue(dq2 == dq1)
        # check that if we convert to homogeneous matrix and back, we get the same result
        double_conv2 = DualQuaternion.from_homogeneous_matrix(dq2.homogeneous_matrix())
        self.assertTrue(dq2 == double_conv2)

    def test_dual_number_conjugate(self):
        # dual number conjugate doesn't behave as you would expect given its special definition
        # (dq1 @ dq2)* ?= dq1* @ dq2*  This is a different order than the other conjugates!
        res1 = (self.random_dq * self.other_random_dq).dual_number_conjugate()
        res2 = self.random_dq.dual_number_conjugate() * self.other_random_dq.dual_number_conjugate()
        self.assertTrue(res1 == res2)

    def test_combined_conjugate(self):
        dq = self.normalized_dq * self.normalized_dq.combined_conjugate()
        # a normalized quaternion multiplied with its combined conjugate should yield unit rotation
        self.assertAlmostEqual(dq.q_r, quaternion.one)
        # (dq1 @ dq2)* ?= dq2* @ dq1*
        res1 = (self.random_dq * self.other_random_dq).combined_conjugate()
        res2 = self.other_random_dq.combined_conjugate() * self.random_dq.combined_conjugate()
        self.assertTrue(res1 == res2)

    def test_normalize(self):
        self.assertTrue(self.unit_dq.is_normalized())
        self.assertEqual(self.unit_dq.normalized(), self.unit_dq)
        unnormalized_dq = DualQuaternion.from_quat_pose_array([1, 2, 3, 4, 5, 6, 7])
        unnormalized_dq.normalize()  # now normalized!
        self.assertTrue(unnormalized_dq.is_normalized())

    def test_transform(self):
        # transform a point from one frame (f2) to another (f1)
        point_f2 = [1, 1, 0]
        self.assertEqual(self.unit_dq.transform_point(point_f2), point_f2)

        # test that quaternion transform and matrix transform yield the same result
        T_f1_f2 = np.array([[1, 0, 0, 2], [0, 0.5403, -0.8415, 3], [0, 0.8415, 0.5403, 1], [0, 0, 0, 1]])
        dq_f1_f2 = DualQuaternion.from_homogeneous_matrix(T_f1_f2)

        # point is in f2, transformation will express it in f1
        point_f1_matrix = np.dot(T_f1_f2, np.expand_dims(np.array(point_f2 + [1]), 1))
        point_f1_dq = np.array(dq_f1_f2.transform_point(point_f2))
        try:
            np.testing.assert_array_almost_equal(point_f1_matrix[:3].T.flatten(), point_f1_dq.flatten(), decimal=3)
        except AssertionError as e:
            self.fail(e)

    def test_saving_loading(self):
        # get the cwd so we can create a couple test files that we'll remove later
        dir = os.getcwd()
        self.unit_dq.save(dir + '/identity.json')
        # load it back in
        loaded_unit = DualQuaternion.from_file(dir + '/identity.json')
        self.assertEqual(self.unit_dq, loaded_unit)
        # clean up
        os.remove(dir + '/identity.json')

    def test_loading_illegal(self):
        self.assertRaises(IOError, DualQuaternion.from_file, 'boguspath')
