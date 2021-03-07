package com.rocketdonkey.nongofit.metrics

import androidx.lifecycle.LiveData

/**
 * A metric is an object that returns a single value of interest via its `get` method.
 *
 * More docs...
 */
interface Metric {
    fun get()
}

// Each possible metric has its own interface since each metric has a different type. There is
// likely way to use a single interface for this (e.g. have a `Value` return type that wrapped the
// actual value), but this is simple and solves the current issues.

interface ElapsedTimeMetric {
    fun get(): LiveData<Int>
}

interface SpeedMetric {
    fun get(): LiveData<Double>
    fun increase(amount: Double)
    fun decrease(amount: Double)
}

interface DistanceMetric {
    fun get(): LiveData<Double>
}

interface InclineMetric {
    fun get(): LiveData<Double>
    fun increase(amount: Double)
    fun decrease(amount: Double)
}
