import astropy.modeling.models
import numpy as np
import scipy.stats

_gauss_StDev_to_FWHM = (2 * np.sqrt(2 * np.log(2)))  # conversion constant


class GaussianModel1D(astropy.modeling.models.Gaussian1D):
    """ Improvement on the astropy gaussian function to provide integration
     abilities and some basic conversions.

        A Gaussian is described by 3 terms, the height a, the position of the
         center / mean b and the stdev c.

        $f\left(x\right) = a \exp{\left(- { \frac{(x-b)^2 }{ 2 c^2} } \right)}$
    """

    def __init__(self, amplitude=None, mean=0., stddev=None, fwhm=None,
                 flux=None, **kwargs):
        """ This improves on the standard gaussian in astropy by allowing you
        to define a gaussian by the integral and the FWHM in class. This
        results in somevar checking in initialisation.

        You must give the stddev OR FWHM, and the flux OR the amplitude

        :param amplitude: amplitude (peak) of gaussian
        :type amplitude: float
        :param mean: mean value
        :type mean: float
        :param stdev: standard deviation
        :type stddev: float
        :param fwhm: full width at half maximum
        :type fwhm: float
        :param flux: Integral of the gaussian, requires stdev or fwhm to be set
        :type flux: float
        """

        if not ((stddev is not None) ^ (fwhm is not None)):
            raise ValueError(
                "You must set either fwhm OR stdev, not both or  neither. "
                "got stdev={} fwhm={}".format(stddev, fwhm))

        if not ((flux is not None) ^ (amplitude is not None)):
            raise ValueError(
                "You must set either amplitude OR flux, not both or neither."
                " got amplitude={} flux={}".format(amplitude, flux))

        # initialise empty gaussian, then we fill in values
        astropy.modeling.models.Gaussian1D.__init__(self, 1., mean, 1.,
                                                    **kwargs)

        if stddev is not None:
            self.stddev = stddev
        else:
            self.fwhm = fwhm  # this sets stdev

        if amplitude is not None:
            self.amplitude = amplitude
        else:
            self.flux = flux  # this sets the amplitude

    @property
    def flux(self):
        """ Calculates the Flux of the gaussian model (integration between
         infinities)

        $\text{flux} = \int_{-\infty}^\infty a e^{- { (x-b)^2 \over 2 c^2 } }\,
        dx=ac\cdot\sqrt{2\pi}.$

        :return: the flux
        """

        flux = self.amplitude * (self.stddev * np.sqrt(2 * np.pi))
        return flux

    @flux.setter
    def flux(self, flux):
        """ Sets the height of the gaussian given a flux. This uses the stdev
         and so that should be set first.

         $\text{flux} = \int_{-\infty}^\infty a e^{- { (x-b)^2 \over 2 c^2 } }
         \,dx=ac\cdot\sqrt{2\pi}.$
         $a = \frac{\text{flux}}{c \sqrt{2 \pi}}$

        :param flux:
        :type flux: float

        :param flux: integral of the gaussian
        """

        self.amplitude = flux / (self.stddev * np.sqrt(2 * np.pi))

    @property
    def fwhm(self):
        """ The FWHM is defined as $\mathrm{FWHM} = 2 \sqrt{2 \ln 2}\ c \approx
         2.35482 c.$

        This function uses the constant _gauss_StDev_to_FWHM defined at the top
         of this file

        :return: fwhm
        """

        fwhm = self.stddev * _gauss_StDev_to_FWHM
        return fwhm

    @fwhm.setter
    def fwhm(self, fwhm):
        """ Sets the stdev of the gaussian from the FWHM

        $\mathrm{FWHM} = 2 \sqrt{2 \ln 2}\ c \approx 2.35482 c.$

        This function uses the constant _gauss_FWHM_to_StDev defined at the
         top of this file


        :param fwhm: Full width at half maximum
        :type fwhm: float
        :return:
        """

        self.stddev = fwhm / _gauss_StDev_to_FWHM

    def integrate(self, limits):
        """ Integrates the model over the given limits (i.e [0,1,2] would
         give 0->1, 1->2) using the cumulative distribution function $\Phi$
         (scipy.stats.norm.cdf) to obtain the flux binned between the limits.

        $\Phi (z) = \mathrm{Pr}(Z < z) = \frac{1}{\sqrt{2\pi}} \int_{-\infty}^z
         \mathrm{exp}\left( -\frac{u^2}{2} \right) \mathrm{d}u$
        $\mathrm{Pr}(a < X \le b) = \Phi\left(\frac{b-\mu}{\sigma} \right)
        - \Phi\left(\frac{a-\mu}{\sigma} \right) $

        This probability is then turned into a binned flux by multiplying it by
         the total flux

        :param limits: array of limits, i.e [0,1,2]
        :type limits: numpy.ndarray
        """

        cdf = scipy.stats.norm.cdf(limits, self.mean, self.stddev)

        # x+1 - x, [-1] is x_0 - x_n and unwanted
        area = (np.roll(cdf, -1) - cdf)[:-1]

        binned_flux = area * self.flux
        return binned_flux
