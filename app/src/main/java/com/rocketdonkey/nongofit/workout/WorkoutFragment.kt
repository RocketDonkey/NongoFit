package com.rocketdonkey.nongofit.workout

import android.os.Bundle
import androidx.fragment.app.Fragment
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.databinding.DataBindingUtil
import androidx.fragment.app.viewModels
import com.rocketdonkey.nongofit.R
import com.rocketdonkey.nongofit.databinding.FragmentWorkoutBinding
import dagger.hilt.android.AndroidEntryPoint

/**
 * Home page fragment.
 */
@AndroidEntryPoint
class WorkoutFragment : Fragment() {
    /** Model wrapping all state for the current workout. */
    private val workoutModel: WorkoutViewModel by viewModels()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        // Inflate the layout.
        val binding: FragmentWorkoutBinding = DataBindingUtil.inflate(
            inflater, R.layout.fragment_workout, container, false
        )

        // Observe LiveData with the lifecycle of this fragment.
        binding.lifecycleOwner = this

        // Bind the Workout model.
        binding.workoutModel = workoutModel

        // Set up listeners.

        // TODO: Should not be done here, move to ViewModel.

        // Speed.
        binding.btnSpeedUp.setOnClickListener { workoutModel.increaseSpeed() }
        binding.btnSpeedDown.setOnClickListener { workoutModel.decreaseSpeed() }

        // Incline.
        binding.btnInclineUp.setOnClickListener { workoutModel.increaseIncline() }
        binding.btnInclineDown.setOnClickListener { workoutModel.decreaseIncline() }

        return binding.root
    }
}