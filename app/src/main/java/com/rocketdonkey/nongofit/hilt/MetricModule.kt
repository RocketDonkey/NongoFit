package com.rocketdonkey.nongofit.hilt

import com.rocketdonkey.nongofit.metrics.*
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

// Note that each of these metrics is a Singleton since the LiveData they provide will be
// injected in multiple locations/shared.
@InstallIn(SingletonComponent::class)
@Module
abstract class MetricModule {
    @Binds
    @Singleton
    abstract fun bindElapsedTimeMetric(impl: ManualElapsedTimeMetric) : ElapsedTimeMetric

    @Binds
    @Singleton
    abstract fun bindPaceMetric(impl: ManualSpeedMetric) : SpeedMetric

    @Binds
    @Singleton
    abstract fun bindDistanceMetric(impl: ManualDistanceMetric) : DistanceMetric

    @Binds
    @Singleton
    abstract fun bindInclineMetric(impl: ManualInclineMetric) : InclineMetric
}