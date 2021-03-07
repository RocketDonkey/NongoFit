package com.rocketdonkey.nongofit.workout

import android.text.format.DateUtils
import androidx.lifecycle.*
import com.rocketdonkey.nongofit.metrics.*
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject

@HiltViewModel
class WorkoutViewModel @Inject constructor(
    private val elapsedTimeMetric: ElapsedTimeMetric,
    private val speedMetric: SpeedMetric,
    private val distanceMetric: DistanceMetric,
    private val inclineMetric: InclineMetric
) :
    ViewModel() {
    /**
     * Returns the total elapsed time.
     *
     * This is formatted as 'MM:SS' (< 1 hour) or 'HH:MM:SS` (> 1 hour).
     */
    fun elapsedTime(): LiveData<String> {
        return Transformations.map(elapsedTimeMetric.get()) { seconds ->
            DateUtils.formatElapsedTime((seconds ?: 0).toLong())
        }
    }

    /**
     * Display value for current speed (MPH).
     */
    fun speed(): LiveData<String> {
        return Transformations.map(speedMetric.get()) { it.toString() }
    }

    fun increaseSpeed() {
        speedMetric.increase(0.5)
    }

    fun decreaseSpeed() {
        speedMetric.decrease(0.5)
    }

    /**
     * Display value for total distance covered.
     *
     * Output is formatted with three points of precision (e.g. 1.234).
     */
    fun totalDistance(): LiveData<String> {
        return Transformations.map(distanceMetric.get()) { String.format("%.3f", it) }
    }

    /**
     * Display value for total distance covered.
     */
    fun incline(): LiveData<String> {
        return Transformations.map(inclineMetric.get()) { it.toString() }
    }

    override fun onCleared() {
//        liveData.removeObserver(observer)
        super.onCleared()
    }
}