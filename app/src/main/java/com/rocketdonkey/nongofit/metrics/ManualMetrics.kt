package com.rocketdonkey.nongofit.metrics

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.Transformations
import java.util.*
import javax.inject.Inject

/**
 * Manual metrics are ones where the calculations are done 'manually'. For example, rather than
 * reading the distance traveled via a device, the value is calculated using other inputs.
 */

// Time constants used in calculations.
const val SECONDS_PER_HOUR: Double = 3600.0
const val MILLIS_PER_SECOND: Double = 1000.0

/**
 * ElapsedTime metric that is calculated 'manually' by incrementing a counter every 1 second.
 */
class ManualElapsedTimeMetric @Inject constructor() : ElapsedTimeMetric {
    private val timer = Timer()

    /** The total number of seconds elapsed since the metric started tracking. */
    private val _elapsedSeconds = MutableLiveData<Int>()
    private val elapsedSeconds: LiveData<Int> get() = _elapsedSeconds

    init {
        timer.scheduleAtFixedRate(object : TimerTask() {
            override fun run() {
                _elapsedSeconds.postValue((elapsedSeconds.value ?: 0) + 1)
            }
        }, 0, 1000)
    }

    override fun get(): LiveData<Int> = elapsedSeconds
}

/**
 * PaceMetric that is manually modified in response to user input.
 */
class ManualSpeedMetric @Inject constructor() : SpeedMetric {
    private val _pace = MutableLiveData<Double>(3.5)
    private val pace: LiveData<Double> get() = _pace

    override fun get(): LiveData<Double> = pace
    override fun increase(amount: Double) {
        _pace.value = (_pace.value ?: 0.0) + amount
    }

    override fun decrease(amount: Double) {
        _pace.value = (_pace.value ?: 0.0) - amount
    }
}

/**
 * DistanceMetric that is manually calculated based on pace changes.
 */
class ManualDistanceMetric @Inject constructor(speedMetric: SpeedMetric) :
    DistanceMetric {
    private val timer = Timer()
    private val tickInterval: Long = 500

    /** Speed in MPH (will need to redo if we ever move to Europe). */
    private var currentSpeed = 0.0

    private val _totalDistance = MutableLiveData<Double>()
    private val totalDistance: LiveData<Double> get() = _totalDistance

    init {
        // When the speed changes the amount of distance covered per tick also changes.
        Transformations.distinctUntilChanged(speedMetric.get()).observeForever { speed ->
            currentSpeed = speed
        }

        timer.scheduleAtFixedRate(object : TimerTask() {
            override fun run() = calculateDistance()
        }, 0, tickInterval)
    }

    /**
     * Distance (miles) calculation:
     *
     *              currentSpeed                  1hr
     *   --------------------------------  *  -------------
     *   (millisPerSecond / tickInterval)     secondsInHour
     */
    private fun calculateDistance() {
        val distanceSinceLastTick: Double = currentSpeed /
                ((MILLIS_PER_SECOND / tickInterval) * SECONDS_PER_HOUR)
        _totalDistance.postValue((_totalDistance.value ?: 0.0) + distanceSinceLastTick)
    }

    override fun get(): LiveData<Double> = totalDistance
}

/**
 * InclineMetric that is manually modified in response to user input.
 */
class ManualInclineMetric @Inject constructor() : InclineMetric {
    private val _incline = MutableLiveData<Double>(3.5)
    private val incline: LiveData<Double> get() = _incline

    override fun get(): LiveData<Double> = incline
    override fun increase(amount: Double) {
        _incline.value = (_incline.value ?: 0.0) + amount
    }

    override fun decrease(amount: Double) {
        _incline.value = (_incline.value ?: 0.0) - amount
    }
}
