# Standard
import os
import pytest
import json

# Third Party
import numpy as np
import matplotlib
matplotlib.use('Agg') # specifically for Travis CI to avoid backend errors
import f90nml as nml

# Local
from gs2_correlation.simulation import Simulation

class TestClass(object):

    def setup_class(self):
        os.system('tar -zxf test/test_run.tar.gz -C test/.')

    def teardown_class(self):
        os.system('rm -rf test/test_run')

    @pytest.fixture(scope='function')
    def run(self):
        sim = Simulation('test/test_config.ini')
        return sim

    def test_init(self, run):
        assert type(run.config_file) == str

    def test_find_file(self, run):
        assert run.find_file_with_ext('.g') == 'test/test_run/v/id_1/v_id_1.g'

    def test_find_file_several_matches(self, run):
        os.system('touch test/test_run/v/id_1/test.out.nc.old')
        assert run.find_file_with_ext('.out.nc') == 'test/test_run/v/id_1/v_id_1.out.nc'

    def test_read(self, run):
        run.read_config()
        assert type(run.domain) == str
        assert type(run.in_file) == str
        assert type(run.in_field) == str
        assert type(run.analysis) == str
        assert type(run.out_dir) == str
        assert type(run.time_slice) == int
        assert type(run.perp_guess_x) == float
        assert type(run.perp_guess_y) == float
        assert type(run.time_interpolate_bool) == bool
        assert type(run.time_interp_fac) == int
        assert type(run.zero_bes_scales_bool) == bool
        assert type(run.zero_zf_scales_bool) == bool
        assert type(run.lab_frame) == bool
        assert (type(run.spec_idx) == int or type(run.spec_idx) == type(None))
        assert type(run.npeaks_fit) == int
        assert type(run.time_guess) == list
        assert type(run.time_guess_grow) == float
        assert type(run.time_guess_dec) == float
        assert type(run.time_guess_osc) == np.ndarray
        assert type(run.time_max) == float
        assert type(run.box_size) == list
        assert type(run.time_range) == list
        assert type(run.par_guess) == list

        assert type(run.amin) == float
        assert type(run.bref) == float
        assert type(run.dpsi_da) == float
        assert type(run.nref) == float
        assert type(run.omega) == float
        assert type(run.rho_ref) == float
        assert type(run.rho_tor) == float
        assert type(run.tref) == float
        assert type(run.vth) == float

        assert type(run.seaborn_context) == str
        assert type(run.write_field_interp_x) == bool

    def test_read_netcdf(self, run):
        field_shape = run.field.shape
        arr_shapes = (run.nt, run.nkx, run.nky, run.ntheta)
        assert field_shape == arr_shapes

    def test_read_netcdf_theta(self, run):
        run.theta_idx = -1
        field_shape = run.field.shape
        arr_shapes = (run.nt, run.nkx, run.nky, run.ntheta)
        assert field_shape == arr_shapes

    def test_read_netcdf_theta_idx_none(self, run):
        run.theta_idx = None
        run.in_field = 'ntot_igomega_by_mode'
        run.read_netcdf()
        field_shape = run.field.shape
        arr_shapes = (run.nt, run.nkx, run.nky, 1, 2)
        assert field_shape == arr_shapes

    def test_read_geometry_file(self, run):
        run.read_geometry_file()
        assert run.geometry.shape[1] > 6

    def test_read_input_file(self, run):
        run.read_input_file()
        assert type(run.input_file) == nml.namelist.Namelist

    def test_read_extracted_input_file(self, run):
        os.system('mv test/test_run/v/id_1/v_id_1.in test/test_run/v/id_1/v_id_1.tmp')
        os.system('mv test/test_run/v/id_1/.v_id_1.in test/test_run/v/id_1/.v_id_1.tmp')
        run.read_config()
        run.read_input_file()
        assert type(run.input_file) == nml.namelist.Namelist
        os.system('mv test/test_run/v/id_1/v_id_1.tmp test/test_run/v/id_1/v_id_1.in')
        os.system('mv test/test_run/v/id_1/.v_id_1.tmp test/test_run/v/id_1/.v_id_1.in')

    def test_time_interpolate(self, run):
        field_shape = run.field.shape
        arr_shapes = (run.nt, run.nkx, run.nky, run.ntheta)
        assert field_shape == arr_shapes

    def test_time_interpolate_4(self, run):
        run.time_interp_fac = 4
        arr_shapes = (run.time_interp_fac*run.nt, run.nkx, run.nky, run.ntheta)
        run.time_interpolate()
        field_shape = run.field.shape
        assert field_shape == arr_shapes

    def test_zero_bes_scales(self, run):
        assert (run.field[:, 1, 1, 0] == 0).all()

    def test_zero_zf_scales(self, run):
        assert (run.field[:, :, 0, :] == 0).all()

    def test_to_lab_frame(self, run):
        run.field = np.ones([51,5,6,9])
        run.to_lab_frame()
        assert np.abs(run.field[5,0,3,0] - np.real(np.exp(1j*3*5*run.omega*run.t[5]))) < 1e-5

    def test_field_to_complex(self, run):
        assert np.iscomplexobj(run.field) == True

    def test_fourier_correction(self, run):
        run.field = np.ones([51, 5, 5, 9])
        run.fourier_correction()
        assert ((run.field[:,:,1:,:] - 0.5) < 1e-5).all()

    def test_field_to_real_space(self, run):
        assert run.field_real_space.shape == (run.nt, run.nx, run.ny)

    def test_domain_reduce(self, run):
        run.box_size = [0.0005, 0.25]
        original_max_x = run.x[-1]
        original_max_y = run.y[-1]
        run.field_real_space = run.field_real_space[:,:,:,np.newaxis]
        run.domain_reduce()
        assert run.x[-1] <= original_max_x
        assert run.y[-1] <= original_max_y

    def test_field_odd_pts(self, run):
        run.field_real_space = np.ones([51,5,6,9])
        run.x = np.ones([5])
        run.nx = 5
        run.y = np.ones([6])
        run.ny = 6
        run.field_odd_pts()
        #print(run.field_real_space.shape)
        assert (np.array(run.field_real_space.shape)%2 == [1,1,1,1]).all()
        assert len(run.t)%2 == 1
        assert len(run.x)%2 == 1
        assert len(run.y)%2 == 1
        assert len(run.dx)%2 == 1
        assert len(run.dy)%2 == 1

    def test_perp_analysis(self, run):
        run.perp_analysis()
        assert len(run.perp_fit_x) == run.nt_slices
        assert len(run.perp_fit_x_err) == run.nt_slices
        assert len(run.perp_fit_y) == run.nt_slices
        assert len(run.perp_fit_y_err) == run.nt_slices

        assert ('corr_x_fit_it_0.pdf' in
                os.listdir('test/test_run/v/id_1/analysis/perp/ky_fixed/corr_fns_x'))
        assert ('corr_y_fit_it_0.pdf' in
                os.listdir('test/test_run/v/id_1/analysis/perp/ky_fixed/corr_fns_y'))
        assert ('perp_fit_x_vs_time_slice.pdf' in
                os.listdir('test/test_run/v/id_1/analysis/perp/ky_fixed'))
        assert ('perp_fit_y_vs_time_slice.pdf' in
                os.listdir('test/test_run/v/id_1/analysis/perp/ky_fixed'))

        results = json.load(open('test/test_run/v/id_1/analysis/results.json', 'r'))

        assert 'lx_t' in results['perp']
        assert 'lx' in results['perp']
        assert 'lx_t_err' in results['perp']
        assert 'lx_err' in results['perp']
        assert 'ly_t' in results['perp']
        assert 'ly' in results['perp']
        assert 'ly_t_err' in results['perp']
        assert 'ly_err' in results['perp']

    def test_write_results(self, run):
        test_dict = {'test':0}
        run.write_results('test1', test_dict)

        t = json.load(open('test/test_run/v/id_1/analysis/results.json', 'r'))
        assert t['test1']['test'] == 0

    def test_perp_analysis_ky_free(self, run):
        run.ky_free = True
        run.perp_guess_ky = 1
        run.perp_analysis()
        assert len(run.perp_fit_x) == run.nt_slices
        assert len(run.perp_fit_x_err) == run.nt_slices
        assert len(run.perp_fit_y) == run.nt_slices
        assert len(run.perp_fit_y_err) == run.nt_slices
        assert len(run.perp_fit_ky) == run.nt_slices
        assert len(run.perp_fit_ky_err) == run.nt_slices

        assert ('corr_x_fit_it_0.pdf' in
                os.listdir('test/test_run/v/id_1/analysis/perp/ky_free/corr_fns_x'))
        assert ('corr_y_fit_it_0.pdf' in
                os.listdir('test/test_run/v/id_1/analysis/perp/ky_free/corr_fns_y'))
        assert ('perp_fit_x_vs_time_slice.pdf' in
                os.listdir('test/test_run/v/id_1/analysis/perp/ky_free'))
        assert ('perp_fit_y_vs_time_slice.pdf' in
                os.listdir('test/test_run/v/id_1/analysis/perp/ky_free'))
        assert ('perp_fit_ky_vs_time_slice.pdf' in
                os.listdir('test/test_run/v/id_1/analysis/perp/ky_free'))

        results = json.load(open('test/test_run/v/id_1/analysis/results.json', 'r'))

        assert 'ky_t' in results['perp_ky_free']
        assert 'ky' in results['perp_ky_free']
        assert 'ky_t_err' in results['perp_ky_free']
        assert 'ky_err' in results['perp_ky_free']

    def test_field_normalize_perp(self, run):
        run.field_normalize_perp()
        assert run.field_real_space_norm_x.shape == (run.nt, run.nx, run.ny)
        assert run.field_real_space_norm_y.shape == (run.nt, run.nx, run.ny)

    def test_perp_norm_mask(self, run):
        run.perp_corr_x = np.ones([51,5,5])
        run.perp_corr_y = np.ones([51,5,5])
        run.perp_norm_mask()
        assert np.abs(run.perp_corr_x[0,2,0] - 1./5.) < 1e-5
        assert np.abs(run.perp_corr_y[0,0,2] - 1./5.) < 1e-5

    def test_calculate_perp_corr(self, run):
        run.field_normalize_perp()
        run.calculate_perp_corr()
        assert run.perp_corr_x.shape == (run.nt, run.nx, run.ny)
        assert run.perp_corr_y.shape == (run.nt, run.nx, run.ny)

    def test_time_analysis(self, run):
        run.lab_frame = False
        run.time_analysis()

        results = json.load(open('test/test_run/v/id_1/analysis/results.json', 'r'))
        assert 'corr_time' in results['time']
        assert 'corr_time_err' in results['time']
        assert 'tau_c' in results['time']
        assert 'tau_c_err' in results['time']

        assert ('corr_time.pdf' in os.listdir('test/test_run/v/id_1/analysis/time'))
        assert run.field_real_space.shape == (run.nt, run.nx, run.ny)
        assert run.time_corr.shape == (run.nt_slices, run.time_slice,
                                       run.nx, run.ny)
        assert ('corr_fns' in os.listdir('test/test_run/v/id_1/analysis/time'))

    def test_time_analysis_lab_frame(self, run):
        run.lab_frame = True
        run.time_analysis()

        results = json.load(open('test/test_run/v/id_1/analysis/results.json', 'r'))
        assert 'corr_time' in results['time_lab_frame']
        assert 'corr_time_err' in results['time_lab_frame']
        assert 'tau_c' in results['time_lab_frame']
        assert 'tau_c_err' in results['time_lab_frame']

        assert ('corr_time.pdf' in os.listdir('test/test_run/v/id_1/analysis/time_lab_frame'))
        assert run.field_real_space.shape == (run.nt, run.nx, run.ny)
        assert run.time_corr.shape == (run.nt_slices, run.time_slice,
                                       run.nx, run.ny)
        assert ('corr_fns' in os.listdir('test/test_run/v/id_1/analysis/time_lab_frame'))

    def test_field_normalize_time(self, run):
        run.field_normalize_time()
        assert run.field_real_space_norm.shape == (run.nt, run.nx, run.ny)

    def test_time_norm_mask(self, run):
        run.time_corr = np.ones([5, 9, 5, 5])
        run.time_norm_mask(0)
        assert np.abs(run.time_corr[0,4,0,2] - 1./45.) < 1e-5

    def test_par_analysis(self, run):
        run.field_real_space = np.random.randint(0,10,size=[51,5,5,9])
        run.ntheta = 9
        run.par_analysis()

        results = json.load(open('test/test_run/v/id_1/analysis/results.json', 'r'))
        assert 'par_fit_params' in results['par']
        assert 'l_par' in results['par']
        assert 'l_par_err' in results['par']
        assert 'k_par' in results['par']
        assert 'k_par_err' in results['par']

        assert run.par_corr.shape == (51,5,5,9)
        assert ('par_fit_length_vs_time_slice.pdf' in
                os.listdir('test/test_run/v/id_1/analysis/parallel'))
        assert ('par_fit_wavenumber_vs_time_slice.pdf' in
                os.listdir('test/test_run/v/id_1/analysis/parallel'))
        assert ('par_fit_it_0.pdf' in
                os.listdir('test/test_run/v/id_1/analysis/parallel/corr_fns'))

    def test_calculate_l_par(self, run):
        run.calculate_l_par()
        assert run.l_par.shape[0] == len(run.theta)

    def test_calculate_par_corr(self, run):
        run.field_real_space = np.ones([51,5,5,9])
        run.ntheta = 9
        run.calculate_l_par()
        run.calculate_par_corr()
        assert np.abs(np.abs(run.l_par[1] - run.l_par[0]) -
                np.abs(run.l_par[-1]/(run.ntheta-1))) < 1e-5
        assert run.par_corr.shape == (51,5,5,9)

    def test_write_field(self, run):
        run.write_field()
        assert ('ntot_t.cdf' in os.listdir('test/test_run/v/id_1/analysis/write_field'))

    def test_write_field_full(self, run):
        run.field_real_space = np.random.randint(0,10,size=[51,5,5,9])
        run.ntheta = 9
        run.write_field_full()
        assert ('ntot_t.cdf' in os.listdir('test/test_run/v/id_1/analysis/write_field_full'))

    def test_write_field_lab_frame(self, run):
        run.lab_frame = True
        run.write_field()
        assert ('ntot_t_lab_frame.cdf' in os.listdir('test/test_run/v/id_1/analysis/write_field'))
