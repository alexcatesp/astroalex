'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import Step1Environmental from './Step1Environmental';
import Step2Characterization from './Step2Characterization';
import Step3TargetSelection from './Step3TargetSelection';

interface SessionWizardProps {
  sessionId?: string;
  onComplete: () => void;
  onCancel: () => void;
}

export default function SessionWizard({ sessionId, onComplete, onCancel }: SessionWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (sessionId) {
      loadSession();
    } else {
      createNewSession();
    }
  }, [sessionId]);

  const loadSession = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getSession(sessionId!);
      setSession(data);

      // Determinar paso actual basado en el estado de la sesión
      if (data.status === 'step1_context') setCurrentStep(2);
      else if (data.status === 'step2_characterized') setCurrentStep(3);
      else if (data.status === 'step3_target_selected') setCurrentStep(4);
      else if (data.status === 'step4_scout_analyzed') setCurrentStep(5);
    } catch (error) {
      console.error('Error loading session:', error);
    } finally {
      setLoading(false);
    }
  };

  const createNewSession = async () => {
    try {
      setLoading(true);
      const activeProfile = await apiClient.getActiveEquipmentProfile();

      const newSession = await apiClient.createSession({
        name: `Sesión ${new Date().toLocaleDateString()}`,
        date: new Date().toISOString(),
        equipment_profile_id: activeProfile.id,
        location: activeProfile.default_location || {
          latitude: 40.4168,
          longitude: -3.7038,
          timezone: 'Europe/Madrid',
          name: 'Madrid',
        },
      });

      setSession(newSession);
    } catch (error) {
      console.error('Error creating session:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStepComplete = async (stepData: any) => {
    await loadSession();
    setCurrentStep(currentStep + 1);
  };

  if (loading || !session) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Iniciando wizard...</div>
      </div>
    );
  }

  const steps = [
    { number: 1, title: 'Contexto Ambiental', icon: '🌍' },
    { number: 2, title: 'Caracterización', icon: '📷' },
    { number: 3, title: 'Selección de Objetivo', icon: '🎯' },
    { number: 4, title: 'Scout Frame', icon: '🔍' },
    { number: 5, title: 'Plan de Vuelo', icon: '📋' },
  ];

  return (
    <div className="h-full flex flex-col">
      {/* Progress Stepper */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between max-w-5xl mx-auto">
          {steps.map((step, index) => (
            <div key={step.number} className="flex items-center">
              <div className="flex flex-col items-center">
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center text-2xl transition-all ${
                    step.number < currentStep
                      ? 'bg-green-600'
                      : step.number === currentStep
                      ? 'bg-blue-600 shadow-lg shadow-blue-900/50'
                      : 'bg-gray-700'
                  }`}
                >
                  {step.number < currentStep ? '✓' : step.icon}
                </div>
                <div
                  className={`mt-2 text-xs font-medium ${
                    step.number === currentStep ? 'text-white' : 'text-gray-500'
                  }`}
                >
                  {step.title}
                </div>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`w-24 h-1 mx-4 ${
                    step.number < currentStep ? 'bg-green-600' : 'bg-gray-700'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="flex-1 overflow-y-auto">
        {currentStep === 1 && (
          <Step1Environmental
            session={session}
            onComplete={handleStepComplete}
            onCancel={onCancel}
          />
        )}
        {currentStep === 2 && (
          <Step2Characterization
            session={session}
            onComplete={handleStepComplete}
            onBack={() => setCurrentStep(1)}
          />
        )}
        {currentStep === 3 && (
          <Step3TargetSelection
            session={session}
            onComplete={handleStepComplete}
            onBack={() => setCurrentStep(2)}
          />
        )}
        {currentStep === 4 && (
          <div className="p-8 text-center">
            <h2 className="text-2xl font-bold text-white mb-4">Step 4: Scout Frame</h2>
            <p className="text-gray-400">Próximamente...</p>
          </div>
        )}
        {currentStep === 5 && (
          <div className="p-8 text-center">
            <h2 className="text-2xl font-bold text-white mb-4">Step 5: Flight Plan</h2>
            <p className="text-gray-400">Próximamente...</p>
          </div>
        )}
      </div>
    </div>
  );
}
